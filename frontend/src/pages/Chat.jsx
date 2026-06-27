import { useAuth } from "../context/AuthContext";

function Chat() {

    const {

        user,

        logout

    } = useAuth();

    return (

        <div>

            <h1>

                Welcome {user?.name}

            </h1>

            <p>

                {user?.email}

            </p>

            <button

                onClick={logout}

            >

                Logout

            </button>

        </div>

    );

}

export default Chat;