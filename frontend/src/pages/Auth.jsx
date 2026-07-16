import { useState } from "react";

import { login, register } from "../services/auth";

import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

function Auth() {

    const [isLogin, setIsLogin] = useState(true);

    const [name, setName] = useState("");

    const [email, setEmail] = useState("");

    const [password, setPassword] = useState("");

    const [loading, setLoading] = useState(false);

    const [error, setError] = useState("");

    const navigate = useNavigate();

    const {

        login: saveLogin

    } = useAuth();

    async function handleSubmit(e) {

        e.preventDefault();

        setLoading(true);

        setError("");

        try {

            if (isLogin) {

                const response = await login(

                    email,

                    password

                );

                saveLogin(

                    response.data.access_token,

                    {

                        id: response.data.user_id,

                        name: response.data.name,

                        email: response.data.email,

                        role: response.data.role

                    }

                );

                if (response.data.role === "EMPLOYEE"){
                    navigate("/employee");
                }
                else{
                    navigate("/chat");
                }
                

            }

            else {

                await register(

                    name,

                    email,

                    password

                );

                alert(

                    "Registration successful."

                );

                setIsLogin(true);

            }

        }

        catch (err) {

            setError(

                err.response?.data?.detail ||

                "Something went wrong."

            );

        }

        finally {

            setLoading(false);

        }

    }

    return (

        <div>

            <h1>

                SmartTech Support Copilot

            </h1>

            <h2>

                {

                    isLogin

                        ? "Login"

                        : "Register"

                }

            </h2>

            <form

                onSubmit={handleSubmit}

            >

                {

                    !isLogin &&

                    <input

                        placeholder="Name"

                        value={name}

                        onChange={(e) =>

                            setName(e.target.value)

                        }

                    />

                }

                <input

                    type="email"

                    placeholder="Email"

                    value={email}

                    onChange={(e) =>

                        setEmail(e.target.value)

                    }

                />

                <input

                    type="password"

                    placeholder="Password"

                    value={password}

                    onChange={(e) =>

                        setPassword(e.target.value)

                    }

                />

                {

                    error &&

                    <p>{error}</p>

                }

                <button

                    type="submit"

                >

                    {

                        loading

                            ? "Loading..."

                            : isLogin

                                ? "Login"

                                : "Register"

                    }

                </button>

            </form>

            <button

                onClick={() =>

                    setIsLogin(

                        !isLogin

                    )

                }

            >

                {

                    isLogin

                        ? "Create Account"

                        : "Already have an account?"

                }

            </button>

        </div>

    );

}

export default Auth;