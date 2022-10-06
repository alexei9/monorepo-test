import snowflake_builder.utilities.generate_keys as generate_keys
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding


def test_generate_rsa_key_pair():
    private_key, public_key = generate_keys.generate_rsa_key_pair()
    priv_key = serialization.load_pem_private_key(
        private_key.encode('utf-8'),
        password=None,
        backend=None)
    pub_key = serialization.load_pem_public_key(
        public_key.encode('utf-8'),
        backend=None)
    # compare public keys
    pub1 = priv_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    pub2 = pub_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    assert pub1 == pub2
    # compare using signature check
    msg_data = b"Some test data to test keys"
    msg_signature = priv_key.sign(
        msg_data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    pub_key.verify(
        msg_signature,
        msg_data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
