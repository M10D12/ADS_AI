import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Login from './components/Login/Login';
import Register from './components/Register/Register';
// Chamar as páginas criadas em /pages aqui
import { AuthProvider } from './context/AuthContext';
function App() {
 
  // Se quiserem testar algum componente podem chamar e colocar aqui, mas depois apaguem pra n ir pro main
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/reg" element={<Register />} />
        </Routes>
      </Router>
    </AuthProvider >
  );
}

export default App;
