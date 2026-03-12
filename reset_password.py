import os
import secrets
import sys

from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash

print('sys.argv:', sys.argv)
if len(sys.argv) < 2:
    print('Usage: python reset_password.py <username> [new_password]')
    sys.exit(1)

username = sys.argv[1]
print('username arg:', repr(username))
new_password = sys.argv[2] if len(sys.argv) > 2 else secrets.token_urlsafe(12)

os.environ.setdefault('SECRET_KEY', 'test')
app = create_app()

with app.app_context():
    user = User.query.filter_by(username=username).first()
    if not user:
        print('User not found:', username)
        sys.exit(1)

    user.password = generate_password_hash(new_password)
    db.session.commit()
    print('Password reset for', user.username)
    print('New password:', new_password)
