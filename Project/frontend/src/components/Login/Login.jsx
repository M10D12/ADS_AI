import "./Login.css";
import { useState } from "react";
import toast, { Toaster } from 'react-hot-toast';
import axios from "axios";
import { useAuth } from '../../context/AuthContext';


const Login = () => {
    
    const { saveAuth } = useAuth();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const validatePassword = (pwd) => {
        if (pwd.length < 8) {
            return "A palavra-passe deve ter pelo menos 8 caracteres";
        }
        if (!/[A-Z]/.test(pwd)) {
            return "A palavra-passe deve ter pelo menos 1 letra maiúscula";
        }
        if (!/[0-9]/.test(pwd)) {
            return "A palavra-passe deve ter pelo menos 1 número";
        }
    };

    const handleSubmit = (e) => {
        const passwordError = validatePassword(password);
        if (passwordError) {
            toast.error(passwordError);
            return;
        }

        axios.post('/api/login/', {
            email: email,
            password: password
        }).then(async (response) => {
            if(response.status === 200){
                const { Acess_token, Refresh_token } = response.data;
                await saveAuth(Acess_token, Refresh_token);
                toast.success("Login Efetuado com Sucesso!");
            }else{
                toast.error("Erro ao efetuar o login. Tenta novamente.");
            }
        })
    };

    return (
        <div className="login-container">
            <Toaster position="top-right" />
            <p className="ini">Iniciar Sessão</p>
            <form className="login-form">
                <input
                    className="login-input"
                    type="text"
                    id="username"
                    name="username"
                    placeholder="Email..."
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />
                <input
                    className="login-input"
                    type="password"
                    id="password"
                    name="password"
                    placeholder="Password..."
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
            </form>
            <div className="two-buttons">
                <button type="submit" className="login-button" onClick={() => {handleSubmit()}}>
                    Entrar
                </button>
                <div className="register-part">
                    <p>Ainda não tem conta?</p>
                    <button type="submit" className="register-button">
                        Registe-se
                    </button>
                </div>

            </div>

        </div>
    )

}

export default Login;