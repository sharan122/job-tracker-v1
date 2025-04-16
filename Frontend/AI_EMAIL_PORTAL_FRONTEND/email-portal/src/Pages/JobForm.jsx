import React, { useState } from "react";
import { useJobForm } from "../API/api";

const JobForm = () => {
  const jobformMutation = useJobForm();
  const [formData, setFormData] = useState({
    company: "",
    title: "",
    employment_type: "",
    email: "",
    job_description: "",
    location: "",
    salary: "",
    job_url: "",
  });

  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const validateForm = () => {
    let newErrors = {};

    if (!formData.company.trim()) newErrors.company = "Company name is required.";
    if (!formData.title.trim()) newErrors.title = "Job title is required.";
    if (!formData.employment_type.trim()) newErrors.employment_type = "Employment type is required.";
    if (!formData.email.includes("@")) newErrors.email = "Invalid email format.";
    if (!formData.job_description.trim()) newErrors.job_description = "Job description is required.";
    if (!formData.location.trim()) newErrors.location = "Job location is required.";
    if (!formData.salary.trim()) newErrors.salary = "Salary is required.";
    if (!formData.job_url.startsWith("http")) newErrors.job_url = "Invalid job URL.";

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateForm()) {
      jobformMutation.mutate(formData);
      setFormData({
        company: "",
        title: "",
        employment_type: "",
        email: "",
        job_description: "",
        location: "",
        salary: "",
        job_url: "",
      });
    }
  };

  return (
    <div className="d-flex justify-content-center align-items-center vh-100">
      <div className="p-4 bg-white shadow rounded" style={{ width: "50%", minWidth: "400px" }}>
        <h4 className="text-center mb-3">Post a Job</h4>
        <form onSubmit={handleSubmit}>
          <div className="row mb-2">
            <div className="col-md-4">
              <label className="form-label">Company Name</label>
              <input type="text" className="form-control" name="company" value={formData.company} onChange={handleChange} required />
              {errors.company && <div className="text-danger">{errors.company}</div>}
            </div>
            <div className="col-md-4">
              <label className="form-label">Job Title</label>
              <input type="text" className="form-control" name="title" value={formData.title} onChange={handleChange} required />
              {errors.title && <div className="text-danger">{errors.title}</div>}
            </div>
            <div className="col-md-4">
              <label className="form-label">Employment Type</label>
              <select className="form-control" name="employment_type" value={formData.employment_type} onChange={handleChange} required>
                <option value="">Select Type</option>
                <option value="Full-Time">Full-Time</option>
                <option value="Part-Time">Part-Time</option>
              </select>
              {errors.employment_type && <div className="text-danger">{errors.employment_type}</div>}
            </div>
          </div>

          <div className="row mb-2">
            <div className="col-md-4">
              <label className="form-label">Contact Email</label>
              <input type="email" className="form-control" name="email" value={formData.email} onChange={handleChange} required />
              {errors.email && <div className="text-danger">{errors.email}</div>}
            </div>
            <div className="col-md-4">
              <label className="form-label">Location</label>
              <input type="text" className="form-control" name="location" value={formData.location} onChange={handleChange} required />
              {errors.location && <div className="text-danger">{errors.location}</div>}
            </div>
            <div className="col-md-4">
              <label className="form-label">Salary</label>
              <input type="text" className="form-control" name="salary" value={formData.salary} onChange={handleChange} required />
              {errors.salary && <div className="text-danger">{errors.salary}</div>}
            </div>
          </div>

          <div className="mb-2">
            <label className="form-label">Job URL</label>
            <input type="url" className="form-control" name="job_url" value={formData.job_url} onChange={handleChange} required />
            {errors.job_url && <div className="text-danger">{errors.job_url}</div>}
          </div>

          <div className="mb-3">
            <label className="form-label">Job Description</label>
            <textarea className="form-control" name="job_description" value={formData.job_description} onChange={handleChange} rows="2" required></textarea>
            {errors.job_description && <div className="text-danger">{errors.job_description}</div>}
          </div>

          <button type="submit" className="btn btn-primary w-100">Post Job</button>
        </form>
      </div>
    </div>
  );
};

export default JobForm;
