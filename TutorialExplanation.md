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
- We validate whether we are transferring the correct NFT with the `asa_id` parameter.. Each NFT will have separate escrow address.

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

We communicate with the smart contracts through transactions. I believe it is a good practice to separate the creation of transactions in separate functions. Additionally, I want to group the logical functions into separate classes which I call services. If we follow this principle, we can easily recreate the transactions multiple times and interact with the smart contracts more easily. 

In our application we have two kind of services:

- `NFTMarketplace` service that implements all of the interactions with the stateful smart contract. This service enables us to call the methods that are implemented in the `NFTMarketplaceInterface`. On top of that, we have one additional method that deploys the application on the blockchain. So, the `NFTMarketplace` has the following methods: `app_initialization`, `initialize_escrow`, `fund_escrow`, `make_sell_offer` and `buy_nft`. In the UI of the application, I don't use the `stop_sell_offer` method so I haven't implemented it in the service class. It is a good exercise for you to try to implement the necessary transaction in order to execute that method.
- `NFTService` that enables us to do create an NFT, change its credentials and opt-in a user. So, the `NFTService` has the following methods: `create_nft`, `change_nft_credentials` and `opt_in`.

In the following sections we will look into more details how we can create those transactions using the [py-algorand-sdk](https://github.com/algorand/py-algorand-sdk).

## NFTMarketplace

Each instance of the `NFTMarketplace` service will represent a separate stateful smart contract deployed on the network. Each of those contracts is responsible for managing the state of one particular NFT. We initialize the smart contrat with the following code:

```python
class NFTMarketplace:
    def __init__(
            self, admin_pk, admin_address, nft_id, client
    ):
        self.admin_pk = admin_pk
        self.admin_address = admin_address
        self.nft_id = nft_id

        self.client = client

        self.teal_version = 4
        self.nft_marketplace_asc1 = NFTMarketplaceASC1()

        self.app_id = None
```

In addition to the required arguments, in the constructor method of the class we initialize the `NFTMarketplaceASC1` stateful smart contract  which we described earlier. From this object we will be able to obtain the TEAL code that will be submitted to the network. 

The first function that we define, creates and executes the transaction that submits the statefull smart contract on the network.  We achieve this with the code bellow:

```python
def app_initialization(self, nft_owner_address):
        approval_program_compiled = compileTeal(
            self.nft_marketplace_asc1.approval_program(),
            mode=Mode.Application,
            version=4,
        )

        clear_program_compiled = compileTeal(
            self.nft_marketplace_asc1.clear_program(),
            mode=Mode.Application,
            version=4
        )

        approval_program_bytes = NetworkInteraction.compile_program(
            client=self.client, source_code=approval_program_compiled
        )

        clear_program_bytes = NetworkInteraction.compile_program(
            client=self.client, source_code=clear_program_compiled
        )

        app_args = [
            decode_address(nft_owner_address),
            decode_address(self.admin_address),
        ]

        app_transaction = ApplicationTransactionRepository.create_application(
            client=self.client,
            creator_private_key=self.admin_pk,
            approval_program=approval_program_bytes,
            clear_program=clear_program_bytes,
            global_schema=self.nft_marketplace_asc1.global_schema,
            local_schema=self.nft_marketplace_asc1.local_schema,
            app_args=app_args,
            foreign_assets=[self.nft_id],
        )

        tx_id = NetworkInteraction.submit_transaction(
            self.client, transaction=app_transaction
        )

        transaction_response = self.client.pending_transaction_info(tx_id)

        self.app_id = transaction_response["application-index"]

        return tx_id
```

The goal of the function above is to define a Application Create Transaction and submit it on the network. This transaction can receive various kinds of parameters, so we need to setup the ones that we need to use in our application. The necessity for the specific parameters was defined in the `app_initialization` method of the `NFTMarketplaceASC1` contract. We summarize the implementation logic in the following steps: 

- We obtain and compile the clear and the approval program from the stateful smart contract.
- We create an `app_args` array which holds the `nft_owner_address` and the `admin_address`. This array will be passed to the `app_args` field in the application create transaction.
- We pass the `nft_id` in the foreign_assets field parameter of the application create transaction.

If this transaction succeeds, we have successfully deployed the application that will handle the selling and re-selling of the NFT with the this particular `nft_id`. 

We now have the `nft_id` and the `app_id` which are the required parameters for initializing the escrow address. Later on, will we will setup this address as the clawback address in the NFT. With the help of the `nft_escrow` function that we defined in the previous section, we can obtain the escrow address and escrow bytes:

```python
	@property
    def escrow_bytes(self):
        if self.app_id is None:
            raise ValueError("App not deployed")

        escrow_fund_program_compiled = compileTeal(
            nft_escrow(app_id=self.app_id, asa_id=self.nft_id),
            mode=Mode.Signature,
            version=4,
        )

        return NetworkInteraction.compile_program(
            client=self.client, source_code=escrow_fund_program_compiled
        )

    @property
    def escrow_address(self):
        return algo_logic.address(self.escrow_bytes)
```

We now need to implement a `initialize_escrow` function which will execute the corresponding transaction that will setup the escrow address in the stateful smart contract. Note that before calling this function, we need to have changed the management credentials of the NFT. The code for changing the management of the NFT will be explained in the `NFTService`.

```python
def initialize_escrow(self):
        app_args = [
            self.nft_marketplace_asc1.AppMethods.initialize_escrow,
            decode_address(self.escrow_address),
        ]

        initialize_escrow_txn = ApplicationTransactionRepository.call_application(
            client=self.client,
            caller_private_key=self.admin_pk,
            app_id=self.app_id,
            on_complete=algo_txn.OnComplete.NoOpOC,
            app_args=app_args,
            foreign_assets=[self.nft_id],
        )

        tx_id = NetworkInteraction.submit_transaction(
            self.client, transaction=initialize_escrow_txn
        )

        return tx_id
```

After successfully submitting the `initialize_escrow` transaction, the initial state of the stateful smart contract is changed to `AppState.active`. Now, we need to implement the `make_sell_offer` and `buy_nft` methods.

The `make_sell_offer` is just a simple application call transaction where we pass two arguments: the method name and the price for the sell offer. The stateful smart contract will approve the transaction only if the sender of the transaction actually holds the required NFT.

```python
def make_sell_offer(self, sell_price: int, nft_owner_pk):
        app_args = [self.nft_marketplace_asc1.AppMethods.make_sell_offer, sell_price]

        app_call_txn = ApplicationTransactionRepository.call_application(
            client=self.client,
            caller_private_key=nft_owner_pk,
            app_id=self.app_id,
            on_complete=algo_txn.OnComplete.NoOpOC,
            app_args=app_args,
            sign_transaction=True,
        )

        tx_id = NetworkInteraction.submit_transaction(self.client, transaction=app_call_txn)
        return tx_id
```

As usually, in the end we need to implement the most complex method. In order to buy an NFT we need to submit Atomic Transfer of 3 transactions:

1. **Application call transaction** from the buyer to the application call. This is a pretty simple transaction, we pass only the method name as an application argument.
2. **Payment transaction** from the buyer to the seller of the NFT. The amount of this transaction should equal to the amount that is set in the sell offer. 
3. **Atomic transfer transaction** from the escrow address to the buyer. Since the escrow address is the clawback address of the NFT, it is able to transfer the NFT from one address to another. This transaction needs to be signed with a [Logic Signature](https://developer.algorand.org/docs/features/asc1/stateless/modes/#logic-signatures). The transaction is approved only when the TEAL logic in the escrow contract evaluates to true.

The code below describes the implementation for the `buy_nft` function, that creates all of the necessary transactions in order to buy the NFT.

```python
def buy_nft(self, nft_owner_address, buyer_address, buyer_pk, buy_price):
        # 1. Application call txn
        app_args = [
            self.nft_marketplace_asc1.AppMethods.buy
        ]

        app_call_txn = ApplicationTransactionRepository.call_application(client=self.client,
                                                                         caller_private_key=buyer_pk,
                                                                         app_id=self.app_id,
                                                                         on_complete=algo_txn.OnComplete.NoOpOC,
                                                                         app_args=app_args,
                                                                         sign_transaction=False)

        # 2. Payment transaction: buyer -> seller
        asa_buy_payment_txn = PaymentTransactionRepository.payment(client=self.client,
                                                                   sender_address=buyer_address,
                                                                   receiver_address=nft_owner_address,
                                                                   amount=buy_price,
                                                                   sender_private_key=None,
                                                                   sign_transaction=False)

        # 3. Asset transfer transaction: escrow -> buyer

        asa_transfer_txn = ASATransactionRepository.asa_transfer(client=self.client,
                                                                 sender_address=self.escrow_address,
                                                                 receiver_address=buyer_address,
                                                                 amount=1,
                                                                 asa_id=self.nft_id,
                                                                 revocation_target=nft_owner_address,
                                                                 sender_private_key=None,
                                                                 sign_transaction=False)

        # Atomic transfer
        gid = algo_txn.calculate_group_id([app_call_txn,
                                           asa_buy_payment_txn,
                                           asa_transfer_txn])

        app_call_txn.group = gid
        asa_buy_payment_txn.group = gid
        asa_transfer_txn.group = gid

        app_call_txn_signed = app_call_txn.sign(buyer_pk)

        asa_buy_txn_signed = asa_buy_payment_txn.sign(buyer_pk)

        asa_transfer_txn_logic_signature = algo_txn.LogicSig(self.escrow_bytes)
        asa_transfer_txn_signed = algo_txn.LogicSigTransaction(asa_transfer_txn, asa_transfer_txn_logic_signature)

        signed_group = [app_call_txn_signed,
                        asa_buy_txn_signed,
                        asa_transfer_txn_signed]

        tx_id = self.client.send_transactions(signed_group)
        return tx_id
```

With the implementation of this method, we complete the `NFTMarketplace` service.

## NFTService

Every instance of the `NFTService` class will be responsible for a single NFT that lives on the blockchain. In the initializer we need to pass the required arguments for creating an NFT, such as: the address of the creator, the name of the NFT and an optional URL which can hold a [ipfs](https://ipfs.io/) image. 

```python
class NFTService:
    def __init__(
            self,
            nft_creator_address: str,
            nft_creator_pk: str,
            client,
            unit_name: str,
            asset_name: str,
            nft_url=None,
    ):
        self.nft_creator_address = nft_creator_address
        self.nft_creator_pk = nft_creator_pk
        self.client = client

        self.unit_name = unit_name
        self.asset_name = asset_name
        self.nft_url = nft_url

        self.nft_id = None
```

We create the NFT with an Asset Config Transaction. At this point all of the management fields of the NFT are filled. We will change this later on. If we leave the NFT with those management credentials, the stateful smart contract should reject it.

```python
def create_nft(self):
        signed_txn = ASATransactionRepository.create_non_fungible_asa(
            client=self.client,
            creator_private_key=self.nft_creator_pk,
            unit_name=self.unit_name,
            asset_name=self.asset_name,
            note=None,
            manager_address=self.nft_creator_address,
            reserve_address=self.nft_creator_address,
            freeze_address=self.nft_creator_address,
            clawback_address=self.nft_creator_address,
            url=self.nft_url,
            default_frozen=True,
            sign_transaction=True,
        )

        nft_id, tx_id = NetworkInteraction.submit_asa_creation(
            client=self.client, transaction=signed_txn
        )
        self.nft_id = nft_id
        return tx_id
```

Next, we implement a `change_nft_credentials_txn` method that clears all of the credentials of the NFT, except the escrow address.

```python
def change_nft_credentials_txn(self, escrow_address):
        txn = ASATransactionRepository.change_asa_management(
            client=self.client,
            current_manager_pk=self.nft_creator_pk,
            asa_id=self.nft_id,
            manager_address="",
            reserve_address="",
            freeze_address="",
            strict_empty_address_check=False,
            clawback_address=escrow_address,
            sign_transaction=True,
        )

        tx_id = NetworkInteraction.submit_transaction(self.client, transaction=txn)

        return tx_id
```

In the end we need to implement just a simple method that allows a user to opt-in to a particular NFT. This is a really nice property of the Algorand blockchain, it doesn't allow users to receive tokens which they haven't allowed to be stored in their wallets. After a successful opt-in for an Algorand Standard Asset, the user is able to receive it.

```python
 def opt_in(self, account_pk):
        opt_in_txn = ASATransactionRepository.asa_opt_in(
            client=self.client, sender_private_key=account_pk, asa_id=self.nft_id
        )

        tx_id = NetworkInteraction.submit_transaction(self.client, transaction=opt_in_txn)
        return tx_id
```

# Step 5: Algorand TestNet deployment

Finally, we have implemented everything. With the help of the services, we can now easily deploy and test the NFTMarketplace application on the Algorand Testnet. The following [script](https://github.com/Vilijan/NFTMarketplace/blob/main/main.py) simulates making a sell offer and executing it by a particular buyer. From the code below, we can see how everything is nicely abstracted which make the execution of the transactions really convenient. 

```python
nft_service.create_nft()

nft_marketplace_service.app_initialization(nft_owner_address=admin_addr)

nft_service.change_nft_credentials_txn(escrow_address=nft_marketplace_service.escrow_address)

nft_marketplace_service.initialize_escrow()
nft_marketplace_service.fund_escrow()
nft_marketplace_service.make_sell_offer(sell_price=100000, nft_owner_pk=admin_pk)

nft_service.opt_in(buyer_pk)

nft_marketplace_service.buy_nft(nft_owner_address=admin_addr,
                                buyer_address=buyer_addr,
                                buyer_pk=buyer_pk,
                                buy_price=100000)
```

Additionally, I have implemented [UI script](https://github.com/Vilijan/NFTMarketplace/blob/main/app.py) that simulates a simple NFTMarketplace where we sell and buy two particular NFTs. You can watch the video below where I demonstrate how you can use the UI.

#TODO: Add link to the video.
