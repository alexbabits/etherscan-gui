# Auto-py-to-exe 'One File' option requires that you include the following files and folders in the 'Additional Files' section:
# folders: tksvg, etherscan, theme. files: sun-valley.tcl

import sys
import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk
import tksvg
from etherscan import Etherscan
import tempfile, base64, zlib


# ---------------- Exact Paths Solution ----------------

# Exact Paths for .tcl references, needed if you want 'One File' instead of 'One Directory' for PyInstaller .exe standalone.
# resource_path function gets the absolute path to a resource in a PyInstaller-packaged application. 
# If application is a standalone .exe, sys._MEIPASS provides path to temp folder PyInstaller unpacks the resources into.
# If application is not packaged, just returns the original path.

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Gets paths for sun-valley.tcl and dark.tcl. Store dark.tcl path so sun-valley.tcl can access its source properly.
sun_valley_path = resource_path("sun-valley.tcl")
dark_tcl_path = resource_path("theme/dark.tcl").replace("\\", "/") # Convert to Unix-style path for TCL
os.environ['DARK_TCL_PATH'] = dark_tcl_path



# ---------------- Application ----------------
class App(ttk.Frame):

    GWEI = 10**9
    WEI = 10**18

    def __init__(self, parent):
        ttk.Frame.__init__(self)

        # Make the frame responsive. (Widgets will resize based on window size.)
        for index in [0, 1, 2]:
            self.columnconfigure(index=index, weight=1)
        for index in [0, 1]:
            self.rowconfigure(index=index, weight=1)

        self.setup_widgets()
        self.get_eth_price()
        self.get_gas_prices()

    def setup_widgets(self):
        ### PRICE AND GAS ###
        self.price_and_gas_frame = ttk.LabelFrame(self, text="Price & Gas", padding=(20, 10))
        self.price_and_gas_frame.grid(row=0, column=0, padx=(20, 10), pady=(20, 10), sticky="nsew")

        self.eth_price_text = tk.Text(self.price_and_gas_frame, wrap=tk.WORD, height=1, width=20, font=("-size", 15, "-weight", "bold"))
        self.eth_price_text.grid(row=1, column=0, pady=10, sticky='nsew')
        self.eth_price_text.config(state=tk.DISABLED)
        
        self.gas_text = tk.Text(self.price_and_gas_frame, wrap=tk.WORD, height=4, width=20, font=("-size", 15, "-weight", "bold"))
        self.gas_text.grid(row=2, column=0, pady=10, sticky='nsew')
        self.gas_text.config(state=tk.DISABLED)

        self.gasEntryLabel = ttk.Label(self.price_and_gas_frame, text="Enter Gwei Amount", anchor="center", font=("-size", 14, "-weight", "bold"))
        self.gasEntryLabel.grid(row=3, column=0, padx=5, pady=(0, 10), sticky="nsew")

        self.gasEntry = ttk.Entry(self.price_and_gas_frame)
        self.gasEntry.insert(0, "")
        self.gasEntry.grid(row=4, column=0, padx=5, pady=(0, 10), sticky="nsew")

        self.getGasTimeButton = ttk.Button(self.price_and_gas_frame, text="Get Time Estimate", style="Accent.TButton", command=self.get_gas_time_estimate)
        self.getGasTimeButton.grid(row=5, column=0, padx=5, pady=10, sticky="nsew")

        self.gas_time_text = tk.Text(self.price_and_gas_frame, wrap=tk.WORD, height=2, width=20, font=("-size", 15, "-weight", "bold"))
        self.gas_time_text.grid(row=6, column=0, pady=10, sticky="nsew")
        self.gas_time_text.insert(tk.END, "No time estimate")
        self.gas_time_text.config(state=tk.DISABLED)


        ### SETTINGS ###
        self.settings_frame = ttk.LabelFrame(self, text="Settings", padding=(20, 10))
        self.settings_frame.grid(row=1, column=0, padx=(20, 10), pady=(0, 10), sticky="nsew")

        self.switch = ttk.Checkbutton(self.settings_frame, text="Light Mode", style="Switch.TCheckbutton")
        self.switch.grid(row=1, column=0, padx=5, pady=10, sticky="nsew")


        ### ADDRESS LOOKUP ###
        self.addressLookupFrame = ttk.LabelFrame(self, text="Address Lookup", padding=(20, 10))
        self.addressLookupFrame.grid(row=0, column=1, padx=(10,10), pady=(20, 10), sticky="nsew")
        self.addressLookupFrame.columnconfigure(index=0, weight=1)

        self.addressEntryLabel = ttk.Label(self.addressLookupFrame, text="Enter 0x Address", anchor="center", font=("-size", 14, "-weight", "bold"))
        self.addressEntryLabel.grid(row=0, column=0, padx=5, pady=(20, 10), sticky="nsew")

        self.addressEntry = ttk.Entry(self.addressLookupFrame, width=50)
        self.addressEntry.insert(0, "")
        self.addressEntry.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="ew")

        self.getAddressStatusButton = ttk.Button(self.addressLookupFrame, text="Get ETH Balance", style="Accent.TButton", command=self.get_address_status)
        self.getAddressStatusButton.grid(row=2, column=0, padx=5, pady=10, sticky="nsew")

        self.getRecentTxButton = ttk.Button(self.addressLookupFrame, text="Get Recent ERC-20 Transactions",style="Accent.TButton", command=self.get_recent_tx)
        self.getRecentTxButton.grid(row=3, column=0, padx=5, pady=10, sticky="nsew")


        ### TRANSACTION LOOKUP ###
        self.txLookupFrame = ttk.LabelFrame(self, text="Transaction Lookup", padding=(20, 10))
        self.txLookupFrame.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="nsew")
        self.txLookupFrame.columnconfigure(index=0, weight=1)

        self.txEntryLabel = ttk.Label(self.txLookupFrame, text="Enter Tx hash", anchor="center", font=("-size", 14, "-weight", "bold"))
        self.txEntryLabel.grid(row=5, column=0, padx=5, pady=(10, 10), sticky="nsew")

        self.txEntry = ttk.Entry(self.txLookupFrame, width=50)
        self.txEntry.insert(0, "")
        self.txEntry.grid(row=6, column=0, padx=5, pady=(0, 10), sticky="ew")

        self.getTxStatusButton = ttk.Button(self.txLookupFrame, text="Get Tx Status", style="Accent.TButton", command=self.get_tx_status)
        self.getTxStatusButton.grid(row=7, column=0, padx=5, pady=10, sticky="nsew")


        ### RECENT TRANSACTIONS ###
        self.recent_transactions_frame = ttk.LabelFrame(self, text="Recent Transactions", padding=(20, 10))
        self.recent_transactions_frame.grid(row=0, column=2, padx=(10, 0), pady=(25, 5), sticky="nsew")

        self.scrollbar = ttk.Scrollbar(self.recent_transactions_frame)
        self.scrollbar.pack(side="right", fill="y")

        self.recent_tx_text = tk.Text(self.recent_transactions_frame, wrap=tk.WORD, yscrollcommand=self.scrollbar.set, width = 10, height=20)
        self.recent_tx_text.pack(expand=True, fill="both")
        self.scrollbar.config(command=self.recent_tx_text.yview)
        self.recent_tx_text.config(state=tk.DISABLED)

        ### NOTEBOOK & TABS ###
        self.notebook_frame = ttk.LabelFrame(self, text="Notebook", padding=(20, 10))
        self.notebook_frame.grid(row=1, column=2, padx=(10, 0), pady=(5, 5), sticky="nsew")

        self.notebook = ttk.Notebook(self.notebook_frame)
        self.notebook.pack(expand=True, fill="both")

        self.eth_balance_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.eth_balance_tab, text="ETH Balance")

        self.eth_balance_tab_text = tk.Text(self.eth_balance_tab, wrap=tk.WORD, font=("TkDefaultFont", 15, "bold"), width=10, height=10)
        self.eth_balance_tab_text.grid(row=0, column=0, sticky="nsew")
        self.eth_balance_tab_text.insert(tk.END, "No balance data.")
        self.eth_balance_tab_text.config(state=tk.DISABLED)
        self.eth_balance_tab.columnconfigure(0, weight=1)
        self.eth_balance_tab.rowconfigure(0, weight=1)

        self.tx_status_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.tx_status_tab, text="Tx Status")

        self.tx_status_tab_text = tk.Text(self.tx_status_tab, wrap=tk.WORD, font=("TkDefaultFont", 12, "bold"))
        self.tx_status_tab_text.grid(row=0, column=0, sticky="nsew")
        self.tx_status_tab_text.insert(tk.END, "No tx data.")
        self.tx_status_tab_text.config(state=tk.DISABLED)
        self.tx_status_tab.columnconfigure(0, weight=1)
        self.tx_status_tab.rowconfigure(0, weight=1)


    ####################### API CALL FUNCTIONS #######################

    ### AUTOMATED FUNCTIONS ### : Calls itself every 30 seconds to get updated data.
    def get_eth_price(self):
        try:
            etherscan = Etherscan("MY ETHERSCAN API KEY")
            eth_price_data = etherscan.get_eth_last_price()
            eth_usd_price = eth_price_data['ethusd']
            self.update_text_widget(self.eth_price_text, f"ETHUSD: {eth_usd_price}")
        except Exception as e:
            self.update_text_widget(self.eth_price_text, "Couldn't get ETH price.")
            
        self.after(30000, self.get_eth_price)


    def get_gas_prices(self):
        try:
            etherscan = Etherscan("MY ETHERSCAN API KEY")
            gas_data = etherscan.get_gas_oracle()

            last_block = gas_data['LastBlock']
            safe_gas_price = gas_data['SafeGasPrice']
            propose_gas_price = gas_data['ProposeGasPrice']
            fast_gas_price = gas_data['FastGasPrice']

            message = f"Block #: {last_block}\nLow Gas: {safe_gas_price} gwei\nAverage Gas: {propose_gas_price} gwei\nHigh Gas: {fast_gas_price} gwei"
            self.update_text_widget(self.gas_text, message)

        except Exception as e:
            self.update_text_widget(self.gas_text, "Couldn't get gas data.")

        self.after(30000, self.get_gas_prices) 

    ### BUTTON FUNCTIONS ### : One second timeout to prevent spamming API calls.
    def get_gas_time_estimate(self):
        self.getGasTimeButton.config(state=tk.DISABLED)

        gasAmountRaw = self.gasEntry.get()
        try:
            gasAmountInt = int(float(gasAmountRaw))
            gasAmount = gasAmountInt * App.GWEI
        except ValueError:
            self.update_text_widget(self.gas_time_text, "Invalid gas amount entered.")
            self.after(1000, lambda: self.getGasTimeButton.config(state=tk.NORMAL))
            return

        try:
            etherscan = Etherscan("MY ETHERSCAN API KEY")
            gas_time_data = etherscan.get_est_confirmation_time(gas_price=str(gasAmount))
            self.update_text_widget(self.gas_time_text, f"Estimated Time in Seconds: {gas_time_data}")

        except Exception as e:
            self.update_text_widget(self.gas_time_text, "Nope.")
        
        self.after(1000, lambda: self.getGasTimeButton.config(state=tk.NORMAL)) 


    def get_address_status(self):
        self.getAddressStatusButton.config(state=tk.DISABLED)
        
        address = self.addressEntry.get()
        
        if not address or len(address) != 42 or not address.startswith('0x'): 
            self.update_text_widget(self.eth_balance_tab_text, "Invalid Ethereum address!")
            self.after(1000, lambda: self.getAddressStatusButton.config(state=tk.NORMAL))
            return

        try:
            etherscan = Etherscan("MY ETHERSCAN API KEY")
            eth_balance = int(etherscan.get_eth_balance(address=address)) / App.WEI
            total_transactions = int(etherscan.get_proxy_transaction_count(address=address), 16)
            message = f"Balance: {eth_balance:.2f} ETH\nTotal # of Txns: {total_transactions}"
            self.update_text_widget(self.eth_balance_tab_text, message)

        except Exception as e:
            self.update_text_widget(self.eth_balance_tab_text, "Address may not exist, or API/network error.")
        
        self.after(1000, lambda: self.getAddressStatusButton.config(state=tk.NORMAL))
    

    def get_recent_tx(self):
        self.getRecentTxButton.config(state=tk.DISABLED)
        
        address = self.addressEntry.get()
        
        if not address or len(address) != 42 or not address.startswith('0x'): 
            self.update_text_widget(self.recent_tx_text, "Invalid Ethereum address!")
            self.after(1000, lambda: self.getRecentTxButton.config(state=tk.NORMAL))
            return

        try:
            etherscan = Etherscan("MY ETHERSCAN API KEY")
            data = etherscan.get_erc20_token_transfer_events_by_address(address=address, startblock=0, endblock=999999999, sort="desc")
            
            if data and len(data) > 0:
                message = ""
                for i in range(min(10, len(data))):
                    blockNumber = data[i]['blockNumber']
                    timeStamp = datetime.utcfromtimestamp(int(data[i]['timeStamp'])).strftime('%Y-%m-%d %H:%M:%S UTC')
                    hash = data[i]['hash']
                    From = data[i]['from']
                    to = data[i]['to']
                    tokenSymbol = data[i]['tokenSymbol']
                    tokenDecimal = int(data[i]['tokenDecimal'])
                    amount = round(int(data[i]['value']) / 10**tokenDecimal, 2)
                    gasPrice = round(int(data[i]['gasPrice']) / App.GWEI, 1)
                    confirmations = data[i]['confirmations']

                    message += f"Time: {timeStamp}\nBlock: {blockNumber}\nFrom: {From}\nTo: {to}\nToken: {tokenSymbol}\nAmount: {amount}\nGas Price: {gasPrice} gwei\nConfirmations: {confirmations}\nHash: {hash}\n\n"

            else:
                message = "No ERC20 token transfers found for this address."
            
            self.update_text_widget(self.recent_tx_text, message)

        except Exception as e:
            self.update_text_widget(self.recent_tx_text, "Address may not exist, or API/network error.")
        
        self.after(1000, lambda: self.getRecentTxButton.config(state=tk.NORMAL))


    def get_tx_status(self):
        self.getTxStatusButton.config(state=tk.DISABLED)

        txHash = self.txEntry.get()
        
        if not txHash or len(txHash) != 66 or not txHash.startswith('0x'): 
            self.update_text_widget(self.tx_status_tab_text, "Invalid tx hash!")
            self.after(1000, lambda: self.getTxStatusButton.config(state=tk.NORMAL))
            return

        try:
            etherscan = Etherscan("MY ETHERSCAN API KEY")
            tx_status_data = etherscan.get_tx_receipt_status(txhash=txHash)
            tx_status = tx_status_data['status']
            tx_status = "Successful" if tx_status == "1" else "Failed"
            tx_data = etherscan.get_proxy_transaction_by_hash(txhash=txHash)
            tx_gas = int(tx_data['gasPrice'], 16) / App.GWEI
            tx_from = tx_data['from']
            tx_to = tx_data['to']
            tx_block_num = int(tx_data['blockNumber'], 16)
            tx_value = int(tx_data['value'], 16) / App.WEI
            message = f"Status: {tx_status}\nGas Paid (gwei): {tx_gas}\nFrom: {tx_from}\nTo: {tx_to}\nBlock Number: {tx_block_num}\nValue: {tx_value} ETH"
            self.update_text_widget(self.tx_status_tab_text, message)

        except Exception as e:
            self.update_text_widget(self.tx_status_tab_text, "tx hash may not exist, or API/network error.")
        
        self.after(1000, lambda: self.getTxStatusButton.config(state=tk.NORMAL)) 

    ### TEXT UPDATER ### : Makes text editable, deletes current content, inserts new content, makes text uneditable.
    def update_text_widget(self, widget, message):
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        widget.insert(tk.END, message)
        widget.config(state=tk.DISABLED)



# ---------------- Launch Main Window ----------------
if __name__ == "__main__":
    # Make temporary blank/transparent icon.
    ICON = zlib.decompress(base64.b64decode('eJxjYGAEQgEBBiDJwZDBy'
        'sAgxsDAoAHEQCEGBQaIOAg4sDIgACMUj4JRMApGwQgF/ykEAFXxQRc='))

    _, ICON_PATH = tempfile.mkstemp()
    with open(ICON_PATH, 'wb') as icon_file:
        icon_file.write(ICON)

    # initialize main window as root, and replace default feather title icon with transparent icon.
    root = tk.Tk()
    root.title("Etherscan GUI")
    root.iconbitmap(default=ICON_PATH)
    # loads SVG handling capabilities into main window.
    tksvg.load(root)

    # Use tcl interpreter to set sun valley theme, setting to dark mode.
    sun_valley_path = resource_path("sun-valley.tcl")
    root.tk.call("source", sun_valley_path)
    root.tk.call("set_theme", "dark")
    # Create instance of the app, allows for filling dimensions and expand if extra space.
    app = App(root)
    app.pack(fill="both", expand=True)

    root.update()
    x_cordinate = int((root.winfo_screenwidth() / 2) - (root.winfo_width() / 2))
    y_cordinate = int((root.winfo_screenheight() / 2) - (root.winfo_height() / 2))
    root.geometry("+{}+{}".format(x_cordinate, y_cordinate))
    root.minsize(root.winfo_width(), root.winfo_height())
    root.mainloop()