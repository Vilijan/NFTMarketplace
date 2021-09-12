# Overview

In this tutorial, you will learn how to develop a simple decentralized application that performs buying and selling of a particular NFT. Multiple instances of this application represent an NFT Marketplace where users can mint, buy and sell NFTs. 
Initially, a user will mint the NFT and link it to a Stateful Smart Contract. This contract will hold the implementation logic for the interactions between the seller and the buyer. Additionally, a separate Stateless Smart Contract is responsible for transferring the NFT to the rightful owner.
Besides the application logic, I try to introduce some practices for developing dApps that can be useful for the development of other projects. Those practices aim to make the code more understandable, easily extendable, and interactable with other applications.

# Step 1: Defining the Stateful Smart Contract Interface

A stateful smart contract represents an application that lives on the Algorand blockchain. Various entities can communicate with the application through application call transactions. Currently, a user-interface application(a mobile app, web app, CLI) creates the transactions and sends them on the network. However, I believe that in the future most of the communication will happen between the smart contracts. This indicates that the smart contracts will initiate the application call transactions. We should note that this feature is still not available on the Algorand blockchain.

The following [document](https://github.com/algorandfoundation/ARCs/blob/6a9f91aed8068bbace872483a64cbf22d0e1c975/ARCs/arc-0004.md) suggests conventions for how to properly structure the communication with the stateful smart contracts. It introduces the concepts of an interface and a method. A single application implements one or multiple interfaces.

> An interface is a logically grouped set of methods. A method is a section of code intended to be invoked externally with an application call transaction.

#TODO: Add explanation and link to the Cosimo Bassi State observer.

Coming back to our application, I try to follow those suggestions and first define an `NFTMarketplaceInterface` which contains all of the necessary methods. Those methods define the communication between the stateful smart contract and the external applications. 

```python
class NFTMarketplaceInterface(ABC):
    @abstractmethod
    def initialize_escrow(self, escrow_address):
        pass

    @abstractmethod
    def make_sell_offer(self, sell_price):
        pass

    @abstractmethod
    def buy(self):
        pass

    @abstractmethod
    def stop_sell_offer(self):
        pass
```

The interface is represented as an abstract python class. The smart contract that wants to conform to this interface will need to implement all of the methods defined in it. It is important to note that multiple smart contracts can conform to this interface, while each of the smart contracts can have separate implementation logic. Despite the different implementation logic, the external communication will remain the same. 

We define four methods in the `NFTMarketplaceInterace`:

- `initialize_escrow(escrow_address)` - initializes the escrow address that is responsible for transferring the NFT. We can even extract this function in a separate interface, but I didn't want to overcomplicate things. 
- `make_sell_offer(sell_price)` - makes a sell offer for the NFT for a particular *sell_price*. The smart contract in this tutorial will directly sell the NFT for the particular *sell_price*, while another contract that conforms to this protocol may decide to sell the NFT through a bidding process. You can check the following [solution](https://developer.algorand.org/solutions/asa-bidding-application-using-pyteal/) that explains how you can sell your NFT through an auction.
- `buy()` - a user buys the NFT that is on the sell offer.
- `stop_sell_offer()` - ends the current selling offer for the NFT.

# Step 2: Implementation of the Stateful Smart Contract

The next step for us is to create a concrete class `NFTMarketplaceASC1` that implements the `NFTMarketplaceInterace`. This class will hold all of the PyTeal logic for the stateful smart contract. In this section, I will explain every code block of the `NFTMarketplaceASC1` smart contract.

## Defining the constants

Every stateful smart contract can contain local and global state which makes the [state data](https://developer.algorand.org/docs/features/asc1/stateful/hello_world/#state-data) of the application. Those states are represented as key-value pairs. It is a good practice to define the keys as constants. This make the code more readable and less error prone.  Additionally, a schema defines the number of integers and bytes in the key-value pairs. A smart contract has a global schema for the global state and local schema for the local state. 

```python
class NFTMarketplaceASC1(NFTMarketplaceInterface):
    class Variables:
        escrow_address = Bytes("ESCROW_ADDRESS")
        asa_id = Bytes("ASA_ID")
        asa_price = Bytes("ASA_PRICE")
        asa_owner = Bytes("ASA_OWNER")
        app_state = Bytes("APP_STATE")
        app_admin = Bytes("APP_ADMIN")

    class AppMethods:
        initialize_escrow = "initializeEscrow"
        make_sell_offer = "makeSellOffer"
        buy = "buy"
        stop_sell_offer = "stopSellOffer"

    class AppState:
        not_initialized = Int(0)
        active = Int(1)
        selling_in_progress = Int(2)
	
	@property
    def global_schema(self):
        return algosdk.future.transaction.StateSchema(num_uints=3,
                                                      num_byte_slices=3)

    @property
    def local_schema(self):
        return algosdk.future.transaction.StateSchema(num_uints=0,
                                                      num_byte_slices=0)
```

In order to make the code more easily understandable and maintainable, I like to separate the constants into multiple classes:

- `Variables` - defines the keys for the global variables used in the smart contract. Those variables represent the global state of the application.
- `LocalVariables` - defines the keys for the local variables used in the smart contract. The `NFTMarketplaceASC1` doesn't have any local variables, that is why we do not have this class.
- `AppMethods` - defines all the methods that enable the communication between the smart contract and the external applications. Each constant in this class needs to be mapped to a unique method defined in a particular interface. 

#### Variables

The contract has six global variables, three integers and three bytes.

- `escrow_address` - contains the address of the stateless smart contract which is responsible for transferring of the [ASA](https://developer.algorand.org/docs/features/asa/) i.e NFT.
- `asa_id` - an unique identifier for the NFT. The smart contract is responsible for the buying and selling of the NFT which matches this id.
- `asa_price` - represents the price of the NFT when a sell offer is active.
- `asa_owner` - contains the address of the current owner of the NFT. Only this address is able to make a sell offer for the NFT.
- `app_state` -  represents one of the possible application states defined in the `AppState` class. Those are the three possible states:
  - `not_initialized` - the smart contract is deployed on the network but the escrow has not been initialized. When the contract is in this state only the `initialize_escrow` method can be executed.
  - `active` -  the `asa_owner` and the NFT has been linked to the contract. However, the NFT is still not on sale meaning that the owner has not initiated a sell offer yet. 
  - `selling_in_progress` - the owner has put the NFT on sale. When the application is in this state, a buyer can execute the `buy` method and purchase the NFT.
- `app_admin` -  contains the address of the admin. Only this address is able to setup the `escrow_address` through a call to the `initialize_escrow` method. 

#### Application methods

The stateful smart contract implements the `NFTMarketplaceInterace` which contains four methods. Thereby we create an `AppMethods` class that uniquely identifies those methods:

- `initialize_escrow` - configures the `escrow_address` in the smart contract. The logic allows the method to be invoked only through an application call made by the `app_admin` address. Additionally, the `escrow_address` can be initialized only once.
- `make_sell_offer` -  the `asa_owner` address is allowed to invoke this method in order to set the NFT on sale for some fixed price of `asa_price` micro algos.
- `buy` - when the NFT is on sale, a buyer is able to invoke this method and buy the NFT.
- `stop_sell_offer` - the `asa_owner` is able to invoke this method in order to stop the current sell offer for the NFT.

Additionally, we have one special method `app_initialization`. We are calling this method when [we first deploy the smart contract](https://developer.algorand.org/docs/features/asc1/stateful/#creating-the-smart-contract) on the network using an application create transaction. You can think of this method as being the constructor of the smart contract, it gets called only when the application is deployed on the network.

## Application initialization

In order to deploy the application on the network, we need three required arguments: the address which currently holds the NFT, the address which has admin rights in the application and the ID of the NFT. We pass the `asa_owner` and the `app_admin` as application arguments, while the `asa_id` is sent in the `foreign_assets` field of the `ApplicationCreateTxn`.

You can read more about the [assets](https://pyteal.readthedocs.io/en/latest/api.html#pyteal.TxnObject.assets) field in the PyTeal documentation. This is a really powerful feature, it can enable stateful smart contracts to look up information about assets and account balances. You can read more about it on the following [link](https://pyteal.readthedocs.io/en/latest/assets.html).

```python
def app_initialization(self):
     return Seq([
     	 Assert(Txn.application_args.length() == Int(2)),
     	 App.globalPut(self.Variables.app_state, self.AppState.not_initialized),
         App.globalPut(self.Variables.asa_id, Txn.assets[0]),
         App.globalPut(self.Variables.asa_owner, Txn.application_args[0]),
         App.globalPut(self.Variables.app_admin, Txn.application_args[1]),
         Return(Int(1))
     ])
```



 ## Initialize escrow

After successful deployment of the application, the admin first needs to call the `initialize_escrow` method in order to setup the stateless contract which will be responsible for transferring the NFT. We achieve this by setting up the address of the stateless smart contract as the [clawback address](https://developer.algorand.org/docs/reference/transactions/#asset-clawback-transaction) of the NFT.

In order to have persistent logic in the application, we make the NFT frozen as well. This removes the ability from the user to be able to send the NFT to an arbitrary address. One way to remove this constraint would be to add a `gift` method in the `NFTMarketplaceASC1` smart contract, which will allow the `asa_owner` to be able to send the NFT for free to anyone. I haven't implemented this feature so I leave this as an exercise for you :)

When we call this method, we want to check whether all the properties in the NFT are as we expect them to be. 

- We don't want the NFT to have a manager address. With this requirement we remove the possibility for changing the clawback address of the NFT.  We want the clawback address to be constant because we use and store it in the stateful smart contract.
- We check whether the clawback address of the NFT is the equal to the escrow address which we pass as an argument.
- We want the NFT to be frozen. If this wasn't the case, one would be able to send the NFT to some address while the `asa_owner` state variable would not get changed.

In the code below I use the AssetParam group of expressions, you can read more about it on the official [PyTeal documentation]().

```python
 def initialize_escrow(self, escrow_address):
        curr_escrow_address = App.globalGetEx(Int(0), self.Variables.escrow_address) 

        asset_escrow = AssetParam.clawback(Txn.assets[0])
        manager_address = AssetParam.manager(Txn.assets[0])
        freeze_address = AssetParam.freeze(Txn.assets[0])
        reserve_address = AssetParam.reserve(Txn.assets[0])
        default_frozen = AssetParam.defaultFrozen(Txn.assets[0])

        return Seq([
            curr_escrow_address,
            Assert(curr_escrow_address.hasValue() == Int(0)), 

            Assert(App.globalGet(self.Variables.app_admin) == Txn.sender()),
            Assert(Global.group_size() == Int(1)),

            asset_escrow,
            manager_address,
            freeze_address,
            reserve_address,
            default_frozen,
            Assert(Txn.assets[0] == App.globalGet(self.Variables.asa_id)),
            Assert(asset_escrow.value() == Txn.application_args[1]),
            Assert(default_frozen.value()),
            Assert(manager_address.value() == Global.zero_address()),
            Assert(freeze_address.value() == Global.zero_address()),
            Assert(reserve_address.value() == Global.zero_address()),

            App.globalPut(self.Variables.escrow_address, escrow_address),
            App.globalPut(self.Variables.app_state, self.AppState.active),
            Return(Int(1))
        ])
```

After successful initialization of the escrow by the admin, the application moves to an `AppState.active` state. Now, the `asa_owner` will be able to make sell offers for the NFT.

## Make sell offer

We sell the NFT through sale offers. Only the NFT owner is able to call the application in order to initiate a sell offer. The application call transaction contains two arguments: the name of the method and the NFT price. This application call will update the internal state from `AppState.active` to `AppState.selling_in_progress`. 

```python
    def make_sell_offer(self, sell_price):
        valid_number_of_transactions = Global.group_size() == Int(1)
        app_is_active = Or(App.globalGet(self.Variables.app_state) == self.AppState.active,
                           App.globalGet(self.Variables.app_state) == self.AppState.selling_in_progress)

        valid_seller = Txn.sender() == App.globalGet(self.Variables.asa_owner)
        valid_number_of_arguments = Txn.application_args.length() == Int(2)

        can_sell = And(valid_number_of_transactions,
                       app_is_active,
                       valid_seller,
                       valid_number_of_arguments)

        update_state = Seq([
            App.globalPut(self.Variables.asa_price, Btoi(sell_price)),
            App.globalPut(self.Variables.app_state, self.AppState.selling_in_progress),
            Return(Int(1))
        ])

        return If(can_sell).Then(update_state).Else(Return(Int(0)))
```

## Buy

The `buy` function is the most complex function in the application. The application call transaction that executes this part of the code needs to be grouped in an [Atomic Transfer](https://developer.algorand.org/docs/features/atomic_transfers/) that contains three transactions:

1. **Application call transaction** that executes the PyTeal code that is located inside the `buy` function. There we make sure that that the application is in `AppState.selling_in_progress` state, the `asa_owner` receives `asa_price` algos, and the `asa_buyer` receives the NFT.
2. **Payment transaction** that pays the right amount of algos to the seller of the NFT. 
3. **Atomic transfer transaction** that transfers the NFT from the current owner to the new owner. The new owner is the sender of the previous two transactions in the Atomic Transfer. 

```python
 def buy(self):
        valid_number_of_transactions = Global.group_size() == Int(3)
        asa_is_on_sale = App.globalGet(self.Variables.app_state) == self.AppState.selling_in_progress

        valid_payment_to_seller = And(
            Gtxn[1].type_enum() == TxnType.Payment,
            Gtxn[1].receiver() == App.globalGet(self.Variables.asa_owner), # correct receiver
            Gtxn[1].amount() == App.globalGet(self.Variables.asa_price), # correct amount 
            Gtxn[1].sender() == Gtxn[0].sender(), # equal sender of the first two transactions, which is the buyer
            Gtxn[1].sender() == Gtxn[2].asset_receiver() # correct receiver of the NFT
        )

        valid_asa_transfer_from_escrow_to_buyer = And(
            Gtxn[2].type_enum() == TxnType.AssetTransfer,
            Gtxn[2].sender() == App.globalGet(self.Variables.escrow_address),
            Gtxn[2].xfer_asset() == App.globalGet(self.Variables.asa_id),
            Gtxn[2].asset_amount() == Int(1)
        )

        can_buy = And(valid_number_of_transactions,
                      asa_is_on_sale,
                      valid_payment_to_seller,
                      valid_asa_transfer_from_escrow_to_buyer)

        update_state = Seq([
            App.globalPut(self.Variables.asa_owner, Gtxn[0].sender()), # update the owner of the ASA.
            App.globalPut(self.Variables.app_state, self.AppState.active), # update the app state
            Return(Int(1))
        ])

        return If(can_buy).Then(update_state).Else(Return(Int(0)))
```

## Stop sell offer

As a final feature of the application, we want to add the possibility for canceling a selling order. If the `asa_owner` no longer wants to sell the NFT, he is able to achieve this by executing an Application call transaction that executes the `stop_selling_offer` method. This is a pretty straight forward method, where we update the internal state of the application from `AppState.selling_in_progress` to `AppState.active` only if the sender of the application is the owner of the NFT.

```python
def stop_sell_offer(self):
        valid_number_of_transactions = Global.group_size() == Int(1)
        valid_caller = Txn.sender() == App.globalGet(self.Variables.asa_owner)
        app_is_initialized = App.globalGet(self.Variables.app_state) != self.AppState.not_initialized

        can_stop_selling = And(valid_number_of_transactions,
                               valid_caller,
                               app_is_initialized)

        update_state = Seq([
            App.globalPut(self.Variables.app_state, self.AppState.active),
            Return(Int(1))
        ])

        return If(can_stop_selling).Then(update_state).Else(Return(Int(0)))
```

# Step 3: Implementation of the Stateless Smart Contract

As we have mentioned earlier, we will use a stateless smart contract as a clawback address for the NFT. We are able to transfer the NFT from one account to another only when the code in the contract evaluates to true.

Most of the logic for the NFTMarketplace application is located in the stateful smart contract, so the escrow contract needs to satisfy only the following conditions:

- The AssetTransfer transaction, which is signed by this contract, is part of an Atomic Transfer. The only way when we transfer the NFT from one address to another is when we execute the `buy` method in the application. 
- We need to check that the first transaction in the Atomic Transfer is calling the correct application. When we compile the code in the escrow contract, as `app_id`we pass the id from the stateful smart contract. 
- We validate whether we are transferring the correct NFT. Each NFT will have separate escrow address.

```python
def nft_escrow(app_id: int, asa_id: int):
    return Seq([
        Assert(Global.group_size() == Int(3)), # atomic transfer with three transactions
        Assert(Gtxn[0].application_id() == Int(app_id)), # we are calling the right application

        Assert(Gtxn[1].type_enum() == TxnType.Payment),

        Assert(Gtxn[2].asset_amount() == Int(1)),
        Assert(Gtxn[2].xfer_asset() == Int(asa_id)), # we are transferring the correct NFT
        Assert(Gtxn[2].fee() <= Int(1000)),
        Assert(Gtxn[2].asset_close_to() == Global.zero_address()),
        Assert(Gtxn[2].rekey_to() == Global.zero_address()),

        Return(Int(1))
    ])
```

With the escrow stateless smart contract, we complete all of the PyTeal code that is part of the NFTMarketplace application. This code will run on the Algorand blockchain. The only thing that is left for us to do is to implement the communication with the contracts.

# Step 4: Communication services



# Step 5: Algorand TestNet deployment



