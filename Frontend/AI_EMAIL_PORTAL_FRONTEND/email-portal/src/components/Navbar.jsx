import { Navbar, Nav, NavDropdown } from "react-bootstrap";
import { useLogout } from "../API/api";
import { Toaster } from "react-hot-toast";
export default function NavbarComponent() {
  const logout = useLogout();
  const user = localStorage.getItem("user") ? JSON.parse(localStorage.getItem("user")) : null;

  return (
    <Navbar bg="dark" variant="dark" expand="lg" className="px-3">
      <Navbar.Brand href="/">AI Email Pro</Navbar.Brand>
      <Navbar.Toggle aria-controls="basic-navbar-nav" />
      <Navbar.Collapse id="basic-navbar-nav">
        <Nav className="ms-auto">
          {user ? (
            <>
              <Nav.Link onClick={() => logout()}>Logout</Nav.Link>
              <NavDropdown title="Profile" id="basic-nav-dropdown">
                <NavDropdown.Item href="/joblist">All Jobs</NavDropdown.Item>
                <NavDropdown.Item href="/myjobs">Applied Jobs</NavDropdown.Item>
                <NavDropdown.Item href="/jobform">Create Job</NavDropdown.Item>
              </NavDropdown>
            </>
          ) : (
            <>
              <Nav.Link href="/register">Register</Nav.Link>
              <Nav.Link href="/login">Login</Nav.Link>
            </>
          )}
        </Nav>
      </Navbar.Collapse>
      <Toaster position="top-right" reverseOrder={false} />
    </Navbar>
  );
}
