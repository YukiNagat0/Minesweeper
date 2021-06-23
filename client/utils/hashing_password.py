import bcrypt

PEPPER = b'$2b$12$CRN45TWTG4B6mt0eWv3YPu'  # Глобальная соль (pepper)


def hash_password(password):
    password = bytes(password, 'UTF-8')
    salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(bcrypt.hashpw(password, PEPPER), salt)
    return hashed_password, salt


def pepper_password(password):
    password = bytes(password, 'UTF-8')
    peppered_password = bcrypt.hashpw(password, PEPPER)

    return peppered_password
