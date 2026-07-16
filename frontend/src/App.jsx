import { Routes, Route } from "react-router-dom";
import Auth from "./pages/Auth";
import Chat from "./pages/Chat";
import ProtectedRoute from "./components/ProtectedRoute";
import EmployeeDashboard from "./pages/EmployeeDashboard";
import EmployeeRoute from "./components/auth/EmployeeRoute";


function App() {

    return (

        <Routes>

            <Route
                path="/"
                element={<Auth />}
            />

            <Route
                path="/chat"
                element={
                    <ProtectedRoute>
                        <Chat />
                    </ProtectedRoute>
                }
            />
            <Route

                path="/employee"

                element={<EmployeeRoute>
                            <EmployeeDashboard />
                        </EmployeeRoute>}

            />

        </Routes>

    );

}

export default App;