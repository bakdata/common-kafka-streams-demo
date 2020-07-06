#!/bin/bash
source ./scripts/create-topic.sh

create_topic "$1" "input-topic"
create_topic "$1" "text-topic"
create_topic "$1" "lemmatized-text-topic"
create_topic "$1" "error-topic"
