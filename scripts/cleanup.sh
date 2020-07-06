#!/bin/bash
source ./scripts/delete-topic.sh


delete_topic "$1" "input-topic"
delete_topic "$1" "text-topic"
delete_topic "$1" "lemmatized-text-topic"
delete_topic "$1" "error-topic"
