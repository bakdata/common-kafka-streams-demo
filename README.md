# Streams Bootstrap and Faust Boostrap Demo

Kafka Streaming NLP pipeline demonstrating how we use Python and Java together for NLP on large text files. It uses the following libraries that introduce common configuration options to Faust and Kafka Streams applications:

- [streams-bootstrap](https://github.com/bakdata/streams-bootstrap) (Java)
- [faust-bootstrap](https://github.com/bakdata/faust-bootstrap) (Python)

The example consists of four different applications:

* Producer: Loads files from a local source directory, uploads them to S3, and sends a record with the corresponding S3 pointer to a specific Kafka topic.
* Loader: Stream processor that processes the records produced by the Producer, loads the content of the files from S3, and uses faust-s3-backed-serializer to serialize the message sent to the output topic.
* spaCy Lemmatizer: Python `faust-bootstrap` application processes the records produced by the Loader, extracts non-stop-word lemmas using spaCy, and sends them as a list serialized with Avro to the output topic.
* TfIDF-Application: Java `streams-bootstrap` application gets documents represented as a list of lemmas as input and calculates the corresponding TFIDF scores.

You can find a [blog post on medium](https://medium.com/bakdata/continuous-nlp-pipelines-with-python-java-and-apache-kafka-f6903e7e429d) with some examples and explanations of how this demo works.

## Getting Started

To run the demo, you can use a Kubernetes cluster with Apache Kafka. To deploy Apache Kafka into a Kubernetes Cluster, you can use the [Confluent Platform Helm chart](https://github.com/confluentinc/cp-helm-charts).
If you test it locally, you can use [minikube](https://github.com/confluentinc/cp-helm-charts#start-minikube).

### Preparation

You can get sample data by running `sh scrips/get-data.sh`, the data will be downloaded and extracted into `./data`. It will contain several text files.

To create the topics you can run `sh scripts/setup.sh <release-name>`. It requires a running [kafka-client](https://github.com/confluentinc/cp-helm-charts/blob/master/examples/kafka-client.yaml) pod.

Add our Kafka application Helm charts:
```bash
helm repo add bakdata-common https://raw.githubusercontent.com/bakdata/streams-bootstrap/master/charts/
```

Moreover, set up an Amazon S3 bucket to use the s3-backed SerDe. You will also need your AWS credentials for the deployment.

### Deploy the Applications

To deploy the Producer, spaCy lemmatizer, and TFIDF Application, you can follow these steps:

#### Build the Container Images

To build the container image for the Java applications, we use [jib](https://github.com/GoogleContainerTools/jib). 
Run the following in the `java`, and `loader` folder and set the image-names:

```bash
./gradlew jibBuildTar --info --image=<image-name>
```

To build the container image for the Python application, use the Dockerfile in the respective folder: 

```bash
docker build . -t spacy-lemmatizer
```
 
#### Push the images to your docker registry

If you run a local minikube cluster, you can refer to [this](https://minikube.sigs.k8s.io/docs/handbook/registry/).

#### Setup the `values.yaml`

Set up the parameters in the  `values.yaml` file for every application with the corresponding image name in your Docker registry. 

#### Deploy the application to your cluster:

Using the `bakdata-common/streams-app` Helm Chart makes it straightforward to deploy KafkaStreams and Faust applications with the proposed common configuration options using the following command:

```bash
helm upgrade --debug --install --recreate-pods --wait --timeout=300 --force \
--values <application>/values.yaml <release> bakdata-common/streams-app
``` 
If you did not set the credentials in the `values.yaml` file you can additionally add the parameters when running helm upgrade:

```bash
helm upgrade --debug --install --force --values values.yaml <release_name> bakdata-common/streams-app \
--set env.AWS_ACCESS_KEY_ID=<acces_key_id> \
--set env.AWS_SECRET_ACCESS_KEY=<access_key> \
--set env.AWS_REGION=<region>
```

### Produce Messages

Finally, you can start to produce messages. To do so, you can either deploy the Producer to the cluster or run it locally.
(Remember to set up your local AWS credential chain.)

Install the dependencies from `requirements.txt` and run:

```bash
python producer.py --broker_url=<borker_urls> --data_path=../data --topic=input-topic --s3_bucket=<s3-bucket-uri> --s3_bucket_dir=input_data
```

## License

This project is licensed under the MIT license. Have a look at the [LICENSE](https://github.com/bakdata/common-kafka-streams-demo/blob/master/LICENSE) for more details.
