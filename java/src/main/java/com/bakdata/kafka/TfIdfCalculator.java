package com.bakdata.kafka;

import com.bakdata.kafka.tfidf.TermFrequency;
import com.bakdata.kafka.tfidf.TfIdfScore;
import java.util.Optional;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.streams.KeyValue;
import org.apache.kafka.streams.kstream.Transformer;
import org.apache.kafka.streams.processor.ProcessorContext;
import org.apache.kafka.streams.state.KeyValueStore;

@Slf4j
@RequiredArgsConstructor
class TfIdfCalculator implements Transformer<String, TermFrequency, KeyValue<String, TfIdfScore>> {
    private final @NonNull String termOccurrenceStoreName;
    private KeyValueStore<String, Long> termOccurrenceStore = null;
    private long minDocumentCount = 0L;

    @SuppressWarnings("unchecked")
    @Override
    public void init(final ProcessorContext context) {
        this.termOccurrenceStore = (KeyValueStore<String, Long>) context.getStateStore(this.termOccurrenceStoreName);
    }

    @Override
    public KeyValue<String, TfIdfScore> transform(final String term, final TermFrequency termFrequency) {
        final double tf = termFrequency.getTf();
        final long termOccurrence = Optional.ofNullable(this.termOccurrenceStore.get(term)).orElse(0L) + 1;
        this.termOccurrenceStore.put(term, termOccurrence);
        final String document = termFrequency.getDocument();
        final long originalDocumentCount = termFrequency.getDocumentCount();
        // if document count has not been updated properly, we know at least that there must be as many documents as
        // the term occurs in or the highest document count we have seen before
        final long documentCount = Math.max(originalDocumentCount, Math.max(termOccurrence, this.minDocumentCount));
        // remember document count for future terms
        this.minDocumentCount = documentCount;
        log.debug("Computing TfIdf for term {} in document {}.", term, document);
        final double idf = Math.log((double) documentCount / termOccurrence);
        final TfIdfScore tfIdfScore = TfIdfScore.newBuilder()
                .setTerm(term)
                .setTfIdf(tf * idf)
                .build();
        return new KeyValue<>(document, tfIdfScore);
    }

    @Override
    public void close() {
        // do not close the key-value store! https://issues.apache.org/jira/browse/KAFKA-4919
    }
}
