from models.user import User, Token


def delete_token(db, token):
    # Look up the token in the database
    db_token = db.query(Token).filter(Token.token == token).first()
    if db_token:
        # Invalidate the token by setting is_active to False
        db_token.is_active = False
        db.commit()
        return True
    return False
