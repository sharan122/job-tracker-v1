import React from "react";
import { Container, Card, Spinner, Alert } from "react-bootstrap";
import { useViewAllJobs, UserAppliedJobs } from "../API/api";

const AppliedJobsPage = () => {
  const { data: jobs, isLoading: jobsLoading, error: jobsError } = useViewAllJobs();
  const { data: appliedJobs, isLoading: appliedLoading, error: appliedError } = UserAppliedJobs();

  console.log("Applied Jobs API Response:", appliedJobs);

  if (jobsLoading || appliedLoading) return <Spinner animation="border" />;
  if (jobsError || appliedError) return <Alert variant="danger">Error loading jobs.</Alert>;

  const appliedJobIds = appliedJobs?.applied_jobs || [];

  const appliedJobList = jobs?.filter((job) => appliedJobIds.includes(job.id)) || [];

  return (
    <Container className="mt-4">
      <h2>Applied Jobs</h2>
      {appliedJobList.length === 0 ? (
        <Alert variant="info">You haven't applied for any jobs yet.</Alert>
      ) : (
        appliedJobList.map((job) => (
          <Card key={job.id} className="mb-3">
            <Card.Body>
              <Card.Title>{job.title}</Card.Title>
              <Card.Text>{job.description}</Card.Text>
              <Card.Text><strong>Company:</strong> {job.company}</Card.Text>
              <Card.Text><strong>Location:</strong> {job.location}</Card.Text>
            </Card.Body>
          </Card>
        ))
      )}
    </Container>
  );
};

export default AppliedJobsPage;
