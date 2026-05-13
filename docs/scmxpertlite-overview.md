# What SCMXPertLite Is and Why Each Tech Is Chosen

SCMXPertLite is a compact enterprise-style learning application built to teach clean source control practices, layered backend design, and the basics of scalable system thinking. It is intentionally small enough for interns to understand quickly, but structured enough to reflect real project conventions used in professional teams.

The project uses **Python** because it is readable, beginner-friendly, and widely used in backend engineering. Python also makes it easier to focus on architecture and clean code rather than language complexity.

**FastAPI** is used for the backend because it is modern, fast, and built around standard HTTP APIs. It gives the team automatic request validation, clear route definitions, and good support for API-first development.

**MongoDB** is a good fit for this stage because the data model is flexible and the project can evolve without heavy schema work. SCMXPertLite is meant to teach design and workflow first, so a document database keeps the setup lightweight.

**Motor** is used for async MongoDB access, and **PyMongo** supports the database interaction layer. This helps the team learn how the API, service layer, and persistence layer stay separated.

**JWT** is used for token-based authentication because it is a common pattern in modern APIs. It supports a stateless login flow and makes the separation between client and server very clear.

**bcrypt** is used for password hashing because passwords must never be stored in plain text. This introduces the idea of security by default, which is important even in learning projects.

**python-dotenv** is used to keep configuration in `.env` files instead of hardcoding secrets. That teaches environment hygiene and helps avoid accidental secret commits.

**Docker** is included in the toolchain so the project can later be packaged and run consistently across machines. Even if Day 1 does not require containers yet, learning Docker early helps interns understand deployment-friendly workflows.

**MongoDB Compass** is useful because it gives a visual way to inspect collections and documents. That makes the data layer easier to understand when the team begins storing users and authentication records.

The frontend uses **HTML, CSS, and JavaScript** because the goal is to keep the client side simple and visible. Interns can then clearly see how a browser talks to an API over HTTP.

Overall, SCMXPertLite is designed to teach four things at once: good repo hygiene, layered backend structure, secure auth basics, and how enterprise systems evolve from simple request-response APIs into more advanced client-server and event-driven designs.
