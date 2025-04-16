import React, { useState } from "react";
import { useLogin } from "../../API/api";
import toast from "react-hot-toast";
const Login = () => {
  const loginMutation = useLogin()
  const [formData, setFormData] = useState({
    username: "",
    password: "",
  });


  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  

  const handleSubmit = (e) => {
    e.preventDefault();
    loginMutation.mutate(formData, {
      onError: (error) => {
        console.log(error.response?.data?.detail);
        toast.error(error.response?.data?.detail || "An error occurred");
      },
    });
  };
  

  return (
    <div className="d-flex justify-content-center align-items-center vh-100">
      <div className="login-container p-3 bg-white shadow rounded" style={{ width: "30%", minWidth: "300px" }}>
        <h4 className="text-center mb-3">Login</h4>
        <form onSubmit={handleSubmit}>
          <div className="mb-2">
            <label className="form-label">Username</label>
            <input type="text" className="form-control form-control-sm" name="username" value={formData.username} onChange={handleChange} required />
          </div>

          <div className="mb-2">
            <label className="form-label">Password</label>
            <input type="password" className="form-control form-control-sm" name="password" value={formData.password} onChange={handleChange} required />
          </div>

          <button type="submit" className="btn btn-primary w-100 btn-sm">
            Login
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;