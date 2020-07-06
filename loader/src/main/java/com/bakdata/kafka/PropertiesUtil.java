package com.bakdata.kafka;

import java.util.Map;
import java.util.Properties;
import lombok.experimental.UtilityClass;
import org.apache.kafka.streams.StreamsConfig;

@UtilityClass
public class PropertiesUtil {
    public static Map<String, Object> originals(final Properties kafkaProperties) {
        return new StreamsConfig(kafkaProperties).originals();
    }
}
