import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { JobApplicationView, useEditApplication, useSendEmail } from '../API/api';

export const JobApplication = () => {
  const sendEmailMutation = useSendEmail()
  const EditApplicationMutation = useEditApplication();
  const { id } = useParams();
  const { data: jobapplication, isLoading } = JobApplicationView(id);

  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    subject: '',
    body: ''
  });

  useEffect(() => {
    if (jobapplication) {
      setFormData({
        subject: jobapplication[0]?.subject || '',
        body: jobapplication[0]?.body || ''
      });
    }
  }, [jobapplication]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevState) => ({
      ...prevState,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    EditApplicationMutation.mutate({ id, data: formData });
    setShowModal(false);
    console.log('Form submitted:', formData);
  };

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-md-8">
          <div className="card border-0 rounded-lg">
            <div className="card-header bg-gradient bg-primary text-white text-center py-3">
              <h3 className="mb-0">Job Application</h3>
            </div>

            <div className="card-body p-4 p-md-5 bg-light">
              {isLoading ? (
                <div className="text-center py-5">
                  <div className="spinner-border text-primary mb-3" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                  <h5 className="fw-bold">AI is generating the email template...</h5>
                  <p className="text-muted">Please wait while we create your job application content.</p>
                </div>
              ) : (
                <div>
                  <div className="mb-4">
                    <div className="d-flex justify-content-between align-items-center mb-2">
                      <h5 className="fw-bold m-0">Subject</h5>
                      <button
                        className="btn btn-outline-primary rounded-pill"
                        onClick={() => setShowModal(true)}
                      >
                        <i className="bi bi-pencil me-1"></i> Edit
                      </button>
                    </div>
                    <div className="p-3 bg-white rounded shadow-sm">
                      {formData.subject}
                    </div>
                  </div>

                  <div className="mb-4">
                    <h5 className="fw-bold">Cover Letter</h5>
                    <div className="p-3 bg-white rounded shadow-sm" style={{ whiteSpace: 'pre-wrap' }}>
                      {formData.body}
                    </div>
                  </div>

                  <div className="text-end mt-4">
                    <button
                      className="btn btn-primary btn-lg px-5 rounded-pill shadow"
                      onClick={() => sendEmailMutation.mutate(jobapplication[0]?.id)}
                      disabled={sendEmailMutation.isLoading} 
                    >
                      {sendEmailMutation.isLoading ? (
                        <>
                          <span className="spinner-border spinner-border-sm me-2"></span>
                          Sending email...
                        </>
                      ) : (
                        <>
                          <i className="bi bi-send me-1"></i>Send Application
                        </>
                      )}
                    </button>
                  </div>

                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {showModal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered modal-lg">
            <div className="modal-content">
              <div className="modal-header bg-primary text-white">
                <h5 className="modal-title">Edit Job Application</h5>
                <button type="button" className="btn-close btn-close-white" onClick={() => setShowModal(false)}></button>
              </div>
              <div className="modal-body">
                <form onSubmit={handleSubmit}>
                  <div className="mb-4">
                    <label htmlFor="subject" className="form-label fw-bold">
                      Subject
                    </label>
                    <input
                      type="text"
                      className="form-control form-control-lg border-0 shadow-sm"
                      id="subject"
                      name="subject"
                      value={formData.subject}
                      onChange={handleChange}
                      required
                    />
                  </div>

                  <div className="mb-4">
                    <label htmlFor="body" className="form-label fw-bold">
                      Cover Letter
                    </label>
                    <textarea
                      className="form-control form-control-lg border-0 shadow-sm"
                      id="body"
                      name="body"
                      rows="8"
                      value={formData.body}
                      onChange={handleChange}
                      required
                    ></textarea>
                  </div>

                  <div className="d-flex justify-content-end gap-2">
                    <button
                      type="button"
                      className="btn btn-outline-secondary px-4 rounded-pill"
                      onClick={() => setShowModal(false)}
                    >
                      Cancel
                    </button>
                    <button type="submit" className="btn btn-primary px-4 rounded-pill">
                      Save Changes
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobApplication;