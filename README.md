# evento
API microservice written in Python3, providing one endpoint which enables the user to search Events from a third party provider.
### Prerequisites
- python3
- make
- pip3

### Run the API
In order to run the API, first make sure you have the prerequisites installed on your machine. Secondly, open your terminal of choice and run the following command: ``make run``
This command will read from the Makefile and execute the run target, making sure that all dependencies are first installed and then run the actual app, by executing api.py file.

### About the endpoint
The API provides the `/search` endpoint which provides a JSON response for events between two date params. Example: `localhost:5000/search?starts_at=2015-07-20T17:32:28Z&ends_at=2021-08-29T14:32:28Z` 