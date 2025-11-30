from database.utils import (
    log_visitor,
    clear_all_visitors,
    print_all_visitors,
    create_user,
    authenticate_user,
    print_all_users,
    clear_all_users,
    create_user_secure
)

#print_all_visitors()
#clear_all_visitors()
log_visitor(name="Test User", purpose="Testing logging functionality")


#create_user_secure("son@example.com", "dadpass", "test@123")
#create_user_secure("hacker@example.com", "hack", "wrongpass")
#create_user("test@example.com", "1234")
#user_ok = authenticate_user("test@example.com", "1234")
#user_bad = authenticate_user("test@example.com", "wrong")
#print("Login correct password:", bool(user_ok))
#print("Login wrong password:", bool(user_bad))
#print_all_users()
#clear_all_users()