import React, { useState, useEffect } from "react";
import { useViewAllJobs, UserAppliedJobs } from "../API/api";
import { useNavigate } from "react-router-dom";
import { useJobApplication } from "../API/api";

const JobListingPage = () => {
  const jobApplicationMutation = useJobApplication();
  const navigate = useNavigate();
  const { data: jobs } = useViewAllJobs();
  const { data: userjobs } = UserAppliedJobs();
  const [selectedJob, setSelectedJob] = useState(null);
console.log(jobs);

  useEffect(() => {
    if (jobs && jobs.length > 0 && !selectedJob) {
      setSelectedJob(jobs[0]);
    }
  }, [jobs, selectedJob]);
console.log(jobs)
  const appliedJobIds = userjobs?.applied_jobs || [];

  const handleJobSelect = (job) => {
    setSelectedJob(job);
  };

  return (
    <div className="container-fluid bg-light min-vh-100 py-4">
      <div className="row justify-content-center">
        <div className="col-lg-10">
          <div className="row">
            <div className="col-md-5">
              <div className="mb-4">
                {jobs && jobs.length > 0 ? (
                  jobs.map((job) => (
                    <div
                      key={job.id}
                      className={`card mb-3 shadow-sm border-0 rounded-3 hover-shadow ${selectedJob && selectedJob.id === job.id ? "border-primary" : ""
                        }`}
                      onClick={() => handleJobSelect(job)}
                      style={{ cursor: "pointer" }}
                    >
                      <div className="card-body">
                        <div className="d-flex justify-content-between align-items-start">
                          <div className="d-flex align-items-center">
                            <div>
                              <span className="d-block fw-bold">{job.company_name}</span>
                            </div>
                          </div>
                        </div>
                        <h5 className="mt-3 fw-bold">{job.title}</h5>
                        <p className="mb-2">{job.location}</p>
                        <p className="text-secondary mb-3">{job.salary}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p>No jobs available</p>
                )}
              </div>
            </div>

            <div className="col-md-7">
              {selectedJob ? (
                <div className="card border-0 shadow-sm rounded-3">
                  <div className="card-body p-4">
                    <div className="d-flex justify-content-between align-items-start mb-4">
                      <div>
                        <h6 className="text-secondary mb-1">{selectedJob.company}</h6>
                        <h3 className="fw-bold mb-2">{selectedJob.title}</h3>
                        <p className="mb-0">{selectedJob.location}</p>
                      </div>

                      {appliedJobIds.includes(selectedJob.id) ? (
                        <button className="btn btn-secondary btn-lg px-4 rounded-pill mb-4" disabled>
                          Applied
                        </button>
                      ) : (
                        <button
                          className="btn btn-danger btn-lg text-white px-4 rounded-pill mb-4"
                          onClick={() => {
                            jobApplicationMutation.mutate(selectedJob.id);
                            navigate(`/jobapplication/${selectedJob.id}`);
                          }}
                        >
                          <span className="font-weight-bold">Apply</span>
                        </button>
                      )}
                    </div>

                    <div className="job-details">
                      <h5 className="fw-bold">Job Description</h5>
                      <p>
                        <strong>Position:</strong> {selectedJob.title}
                      </p>
                      <p>
                        <strong>Location:</strong> {selectedJob.location}
                      </p>
                      <p>
                        <strong>Employment Type:</strong> {selectedJob.employmentType || "Full-Time"}
                      </p>
                      <p>
                        <strong>Salary:</strong> {selectedJob.salary || "Competitive"}
                      </p>
                      <p>
                        <strong>Description:</strong> {selectedJob.job_description || "Competitive"}
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <p>Select a job to view details</p>
              )}
            </div>{" "}
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobListingPage;
