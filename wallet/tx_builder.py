from core.transaction import Transaction


def create_transaction(wallet, utxo, to_address, amount, fee=0.01):
    """
    Build a signed transaction using UTXO model.

    Args:
        wallet: Wallet instance (contains private/public key)
        utxo: UTXOSet instance
        to_address: recipient address
        amount: amount to send
        fee: transaction fee

    Returns:
        Transaction object (signed)
    """

    # ----------------------
    # VALIDATION
    # ----------------------
    if amount <= 0:
        raise Exception("Amount must be greater than 0")

    if fee < 0:
        raise Exception("Fee cannot be negative")

    total_needed = amount + fee

    # ----------------------
    # SELECT UTXOs
    # ----------------------
    inputs, total_available = utxo.find_spendable_utxos(
        wallet.address,
        total_needed
    )

    if total_available < total_needed:
        raise Exception("Insufficient balance")

    # ----------------------
    # BUILD OUTPUTS
    # ----------------------
    outputs = []

    # main transfer
    outputs.append({
        "address": to_address,
        "amount": amount
    })

    # change back to sender
    change = total_available - total_needed

    if change > 0:
        outputs.append({
            "address": wallet.address,
            "amount": change
        })

    # ----------------------
    # CREATE TX (UNSIGNED)
    # ----------------------
    tx = Transaction(inputs, outputs)

    # ----------------------
    # SIGN TRANSACTION
    # ----------------------
    message = tx.to_dict()

    tx.signature = wallet.sign(message)
    tx.public_key = wallet.public_key.to_string().hex()

    # ----------------------
    # FINAL SAFETY CHECK
    # ----------------------
    if not tx.signature or not tx.public_key:
        raise Exception("Transaction signing failed")

    return tx