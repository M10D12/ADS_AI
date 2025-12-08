import "./Register.css";
import { useState } from "react";
import toast, { Toaster } from 'react-hot-toast';
import { useAuth } from '../../context/AuthContext';
import axios from "axios";


const Register = () => {

    const { saveAuth } = useAuth();
    const [nome, setNome] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [passwordConfirm, setPasswordConfirm] = useState("");

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
        if (pwd !== passwordConfirm) {
            return "As palavras-passe não coincidem";
        }
    };

    const handleSubmit = (e) => {

        const passwordError = validatePassword(password);
        if (passwordError) {
            toast.error(passwordError);
            return;
        }

        axios.post('/api/register/', {
            nome: nome,
            email: email,
            password: password
        }).then((response) => {
            if (response.status === 201) {
                toast.success("Conta Criada com Sucesso!");
                setTimeout(() => {
                    // mandar pro login
                }, 2000);
            } else {
                toast.error("Erro ao criar conta. Tente novamente.");
            }
        })
    }

    return (
        <div className="register-container">
            <Toaster position="top-right" />
            <p className="ini">Criar Conta</p>
            <form className="register-form">
                <input
                    className="register-input"
                    type="text"
                    id="username"
                    name="username"
                    placeholder="Nome..."
                    value={nome}
                    onChange={(e) => setNome(e.target.value)}
                    required
                />
                <input
                    className="register-input"
                    type="text"
                    id="username"
                    name="username"
                    placeholder="Email..."
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />
                <input
                    className="register-input"
                    type="password"
                    id="password"
                    name="password"
                    placeholder="Password..."
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
                <input
                    className="register-input"
                    type="password"
                    id="password"
                    name="password"
                    placeholder="Confirma a Password..."
                    value={passwordConfirm}
                    onChange={(e) => setPasswordConfirm(e.target.value)}
                    required
                />
            </form>
            <button type="submit" className="register-button" onClick={() => { handleSubmit() }}>
                Criar Conta
            </button>
        </div>
    )

}

export default Register;