package com.bakdata.kafka;

import static java.util.Collections.emptyMap;

import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;
import com.amazonaws.services.s3.AmazonS3URI;
import com.amazonaws.services.s3.model.S3Object;
import com.amazonaws.util.IOUtils;
import com.bakdata.kafka.util.TopicClient;
import com.bakdata.kafka.util.TopicSettings;
import io.confluent.kafka.streams.serdes.avro.SpecificAvroSerde;
import java.io.IOException;
import java.io.InputStream;
import java.time.Duration;
import java.util.Map;
import java.util.Properties;
import lombok.Setter;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.common.serialization.Serde;
import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.common.serialization.Serdes.StringSerde;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.kstream.KStream;
import org.apache.kafka.streams.kstream.Produced;
import picocli.CommandLine;

@Slf4j
@Setter
@SuppressWarnings("UseOfPropertiesAsHashtable")
public class S3LoaderApplication extends KafkaStreamsApplication {
    private AmazonS3 s3 = AmazonS3ClientBuilder.defaultClient();
    @CommandLine.Option(names = "--s3-backed", arity = "0..1")
    private boolean useS3 = false;
    @CommandLine.Option(names = "--as-text", arity = "0..1")
    private boolean asText = false;

    public static void main(final String[] args) {
        startApplication(new S3LoaderApplication(), args);
    }

    private static Text asDocument(final String text) {
        return Text.newBuilder().setContent(text).build();
    }

    @Override
    public void buildTopology(final StreamsBuilder builder) {
        final KStream<String, String> s3Files = builder.stream(this.getInputTopics());

        final KStream<String, String> texts = s3Files.mapValues(this::loadFromS3);

        // write to output topic
        if (this.asText) {
            texts.mapValues(S3LoaderApplication::asDocument)
                    .to(this.getOutputTopic(), Produced.valueSerde(this.createOutputDocumentSerde()));
        } else {
            texts
                    .to(this.getOutputTopic(), Produced.valueSerde(this.createOutputStringSerde()));
        }
    }

    @Override
    public String getUniqueAppId() {
        return "s3-loader-" + this.getOutputTopic();
    }

    private String loadFromS3(final String key) {
        final AmazonS3URI uri = new AmazonS3URI(key);
        try (final S3Object object = this.s3.getObject(uri.getBucket(), uri.getKey());
                final InputStream input = object.getObjectContent()) {
            log.info("Loading {}", uri);
            return IOUtils.toString(input);
        } catch (final IOException e) {
            throw new RuntimeException("Error reading object " + uri + " from S3", e);
        }
    }

    @Override
    protected void runStreamsApplication() {
        try (final TopicClient topicClient = TopicClient
                .create(PropertiesUtil.originals(this.getKafkaProperties()), Duration.ofSeconds(10L))) {
            final TopicSettings settings = topicClient.describe(this.getInputTopic());
            final Map<String, String> config = emptyMap();
            topicClient.createIfNotExists(this.getOutputTopic(), settings, config);
        }
        super.runStreamsApplication();
    }

    Serde<String> createOutputStringSerde() {
        final Serde<String> serde = this.useS3 ? new S3BackedSerde<>() : Serdes.String();
        final Properties kafkaProperties = this.getKafkaProperties();
        if (this.useS3) {
            kafkaProperties.put(S3BackedSerdeConfig.VALUE_SERDE_CLASS_CONFIG, StringSerde.class);
        }
        final Map<String, Object> config = PropertiesUtil.originals(kafkaProperties);
        serde.configure(config, false);
        return serde;
    }

    Serde<Text> createOutputDocumentSerde() {
        final Serde<Text> serde = this.useS3 ? new S3BackedSerde<>() : new SpecificAvroSerde<>();
        final Properties kafkaProperties = this.getKafkaProperties();
        if (this.useS3) {
            kafkaProperties.put(S3BackedSerdeConfig.VALUE_SERDE_CLASS_CONFIG, SpecificAvroSerde.class);
        }
        final Map<String, Object> config = PropertiesUtil.originals(kafkaProperties);
        serde.configure(config, false);
        return serde;
    }

    @Override
    protected Properties createKafkaProperties() {
        final Properties kafkaProperties = super.createKafkaProperties();
        kafkaProperties.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, StringSerde.class);
        kafkaProperties.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, StringSerde.class);
        return kafkaProperties;
    }
}
