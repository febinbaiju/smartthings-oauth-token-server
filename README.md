# smartthings-oauth-token-server

Lightweight Python server to auto-refresh SmartThings OAuth tokens using a seed refresh token. It saves updated tokens to a file and serves them via HTTP, solving the issue of Personal Access Token expiration in SmartThings API. Perfect for seamless home automation authentication.

## Features

- Automatically fetches and refreshes SmartThings OAuth tokens.
- Stores tokens in a JSON file.
- Serves the latest token via a simple HTTP server.
- Suitable for Docker and containerized environments.
- Easy setup with environment variables or `.env` file.

## Usage

    ### 1. Clone the repository

    ```
    git clone https://github.com/febinbaiju/smartthings-oauth-token-server.git
    cd smartthings-oauth-token-server
    ```

    ### 2. Create `.env` file with your credentials (optional if using docker-compose environment variables)

    ```
    SMARTTHINGS_CLIENT_ID=your_client_id_here
    SMARTTHINGS_CLIENT_SECRET=your_client_secret_here
    REFRESH_TOKEN=your_seed_refresh_token_here
    ```

    ### 3. Build and run with Docker Compose

    ```
    docker-compose up --build -d
    ```

    ### 4. Check logs to confirm token refresh and server startup

    ```
    docker-compose logs -f
    ```

    ### 5. Access the latest token

    Open your browser or curl the token URL:

    ```
    http://localhost:5165/token_info.json
    ```

## Configuration

- **Port**: Default is `5165` (exposed in docker-compose.yml).
- **Token refresh interval**: Every 960 minutes (16 hours).
- **Environment variables**:
  - `SMARTTHINGS_CLIENT_ID` — Your SmartThings OAuth client ID.
  - `SMARTTHINGS_CLIENT_SECRET` — Your SmartThings OAuth client secret.
  - `REFRESH_TOKEN` — The seed refresh token for initial authentication.

## Docker Compose Example

    version: "3.8"
    services:
      token-server:
        build: .
        ports:
          - "5165:5165"
        environment:
          SMARTTHINGS_CLIENT_ID: your_client_id_here
          SMARTTHINGS_CLIENT_SECRET: your_client_secret_here
          REFRESH_TOKEN: your_seed_refresh_token_here
        restart: unless-stopped

## Notes

- The server starts an HTTP server serving `/tmp/token_info.json`.
- It refreshes tokens every 16 hours automatically.
- The initial token is fetched at container startup.
- `.env` file is supported but environment variables via Docker Compose take precedence.
