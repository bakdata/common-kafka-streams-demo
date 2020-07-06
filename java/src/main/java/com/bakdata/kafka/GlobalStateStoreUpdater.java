package com.bakdata.kafka;

import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.streams.processor.Processor;
import org.apache.kafka.streams.processor.ProcessorContext;
import org.apache.kafka.streams.state.KeyValueStore;

@Slf4j
@RequiredArgsConstructor
class GlobalStateStoreUpdater<K, V> implements Processor<K, V> {
    private final @NonNull String stateStoreName;
    private KeyValueStore<K, V> stateStore = null;

    @SuppressWarnings("unchecked")
    @Override
    public void init(final ProcessorContext context) {
        this.stateStore = (KeyValueStore<K, V>) context.getStateStore(this.stateStoreName);
    }

    @Override
    public void process(final K key, final V value) {
        log.info("Updating global state store {} with ({}, {})", this.stateStoreName, key, value);
        this.stateStore.put(key, value);
    }

    @Override
    public void close() {
        // do not close the key-value store! https://issues.apache.org/jira/browse/KAFKA-4919
    }
}