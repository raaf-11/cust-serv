import api from "./api";

export function login(email, password) {

    return api.post(

        "/auth/login",

        {

            email,

            password

        }

    );

}

export function register(

    name,

    email,

    password

) {

    return api.post(

        "/auth/register",

        {

            name,

            email,

            password

        }

    );

}