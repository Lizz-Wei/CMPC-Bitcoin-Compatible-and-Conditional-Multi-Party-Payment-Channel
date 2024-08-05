# Bitcoin-Compatible-and-Conditionality-Multi-Party-Payment-Channel
CMPC is a Bitcoin-compatible multi-party conditional payment channel. It is designed to rely on digital signatures and time locks in order to minimize the requirements for blockchain system scripting functionality. A semi-trusted board of users coordinates user payments and verifies that payment conditions are met.

## Prerequisites

1. **Install Bitcoin Core 0.20.1**:
   - Download Bitcoin Core 0.20.1 from the official [Bitcoin Core website](https://bitcoin.org/en/bitcoin-core/).
   - Install Bitcoin Core by following the instructions provided on the website.

2. **Set Up `bitcoin.conf`**:
   - Configure the `bitcoin.conf` file with the necessary parameters for `regtest` mode. Refer to the provided `bitcoin.conf` file in this repository for the required settings.

## Installation and Setup

1. **Install Bitcoin Core**:
   - Install Bitcoin Core 0.20.1 by following the installation instructions on the official website.

2. **Configure Environment Variables**:
   - Add the path to the Bitcoin Core binaries to your system's environment variables.
     ```
     \path\to\bitcoin-0.20.1\bin
     ```

3. **Run Bitcoin Core**:
   - Open a command line window and run the following command to start Bitcoin Core in `regtest` mode:
     ```bash
     bitcoind -regtest -datadir=\path\to\BitcoinNet -conf=\path\to\bitcoin.conf
     ```

4. **Generate Accounts and UTXOs**:
   - Run `user_gen.py` to generate the required number of users and UTXOs:
     ```bash
     python user_gen.py
     ```

5. **Open and Update Channels**:
   - Run `main.py` to open the payment channels and perform channel updates:
     ```bash
     python main.py
     ```

## Files and Directories

- `bitcoin.conf`: Configuration file for Bitcoin Core in `regtest` mode.
- `user_gen.py`: Script to generate users and UTXOs.
- `main.py`: Main script to open payment channels and perform channel updates.

## Troubleshooting

- Ensure Bitcoin Core is properly installed and the environment variables are correctly set.
- Verify that `bitcoind` is running in `regtest` mode with the correct `datadir` and `conf` file.
- Check the paths in the commands and ensure they match your installation directories.

For any issues or questions, please open an issue in this repository or refer to the Bitcoin Core documentation.
