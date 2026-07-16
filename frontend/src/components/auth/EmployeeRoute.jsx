import { Navigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function EmployeeRoute({ children }) {

    const { user } = useAuth();

    if (!user) {

        return <Navigate to="/" replace />;

    }

    if (user.role !== "EMPLOYEE") {

        return <Navigate to="/chat" replace />;

    }

    return children;

}