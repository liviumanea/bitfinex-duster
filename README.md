# Bitfinex Duster
This project provides a script to convert all currencies in a Bitfinex account into Bitcoin. 

The script uses the Bitfinex API to retrieve account balances, trading pair and ticker information, moves funds from margin into exchange wallets and attempts to convert all wallets either directly into BTC or to USD and then BTC.

## Getting Started

To use this script, you need a Bitfinex account and API credentials. You can obtain API credentials by logging into your Bitfinex account, navigating to the API section, and creating a new API key. Make sure the key has the "Account" and "Read" permissions.

Once you have your API credentials, clone the repository and install the required packages using poetry:

```shell
git clone https://github.com/liviumanea/bitfinex-duster.git
cd bitfinex-duster
pip install poetry
poetry install
```

Provide the following environment variables in an `.env` file in the root directory of the project or as environment variables:

```
BF_API_KEY=<your-api-key>
BF_API_SECRET=<your-api-secret>
BF_API_URL=https://api.bitfinex.com/
```

Run the script using the following command:

```shell
# Get help
poetry run bf-duster --help

# Run the script with defaults
poetry run bf-duster

# Run the script with custom parameters
poetry run bf-duster --max-value-usd 20
```

## To Do
- [ ] Add support for converting to other currencies
- [X] Add support for converting only from wallets below a certain threshold
- [X] Add more testing

## Disclaimer
It is important to note that the use of this program is at your own risk. The author of this program is not responsible for any damages or losses that may occur as a result of using this program. By using this program, you agree to hold the author harmless from any liability or damages that may arise from its use. It is recommended that you thoroughly review and understand the code before using it, and use it in a test environment before using it in a production environment.

