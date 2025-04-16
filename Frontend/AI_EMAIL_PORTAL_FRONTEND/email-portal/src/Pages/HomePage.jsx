import { Container, Row, Col, Button, Card } from "react-bootstrap";
import { motion } from "framer-motion";
import { FaEnvelope, FaRobot, FaCheckCircle } from "react-icons/fa";
import { useNavigate } from "react-router-dom"

export default function HomePage() {
  const navigate = useNavigate()
  const user = localStorage.getItem("user") ? JSON.parse(localStorage.getItem("user")) : null;

  return (
    <div>
      <section className="hero position-relative d-flex align-items-center justify-content-center text-center">
        <div className="overlay position-absolute w-100 h-100" style={{ background: "rgba(0, 0, 0, 0.5)" }}></div>
        <Container className="position-relative">
          <motion.h1
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="display-4 text-light"
          >
            AI-Powered Email Portal
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.2 }}
            className="lead text-light"
          >
            Leverage Gemini AI to generate personalized job opportunity emails effortlessly.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1.5 }}
          >
            {user ? (

              <Button onClick={() => navigate('/joblist')} variant="light" size="lg">Get Started</Button>
            ) : (
              <Button onClick={() => navigate('/login')} variant="light" size="lg">Get Started</Button>

            )}
          </motion.div>
        </Container>
      </section>

      <section className="features py-5">
        <Container>
          <Row className="text-center">
            <Col md={4}>
              <Card className="p-4 border-0 shadow-sm">
                <FaEnvelope size={50} className="text-primary mx-auto mb-3" />
                <h4>Email Automation</h4>
                <p>Generate and send job opportunity emails effortlessly.</p>
              </Card>
            </Col>
            <Col md={4}>
              <Card className="p-4 border-0 shadow-sm">
                <FaRobot size={50} className="text-primary mx-auto mb-3" />
                <h4>AI-Powered Content</h4>
                <p>Utilize Gemini AI to create personalized and effective emails.</p>
              </Card>
            </Col>
            <Col md={4}>
              <Card className="p-4 border-0 shadow-sm">
                <FaCheckCircle size={50} className="text-primary mx-auto mb-3" />
                <h4>Optimized for Success</h4>
                <p>Increase response rates with AI-driven job opportunity emails.</p>
              </Card>
            </Col>
          </Row>
        </Container>
      </section>
    </div>
  );
}