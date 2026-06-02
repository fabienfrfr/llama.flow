import os
import shutil
import pytest
from fastapi.testclient import TestClient
from main import app


# -------------------------
# Fixtures
# -------------------------

@pytest.fixture(scope="session")
def client():
    """
    Create a shared FastAPI test client for all tests.
    """
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_state():
    """ Ensure a clean state directory before each test. """
    state_dir = "user_states"

    if os.path.exists(state_dir):
        shutil.rmtree(state_dir)

    os.makedirs(state_dir)

    yield

    shutil.rmtree(state_dir)


# -------------------------
# Tests
# -------------------------

@pytest.mark.parametrize("user_id", ["u1", "u2", "user123"])
@pytest.mark.parametrize("prompt", ["Hello", "Test", "Ping"])
def test_generate_creates_state_file(client, user_id, prompt):
    """
    Verify that:
    1. The API responds successfully
    2. A state file is created for the user
    3. The state file is not empty
    """
    response = client.post(
        "/generate",
        json={"user_id": user_id, "prompt": prompt}
    )

    assert response.status_code == 200

    state_path = f"user_states/{user_id}.bin"
    assert os.path.exists(state_path)
    assert os.path.getsize(state_path) > 0


def test_state_persists_between_requests(client):
    """Verify that a user's state persists across multiple requests. """
    user_id = "persist"

    # First request creates state
    client.post("/generate", json={"user_id": user_id, "prompt": "Hello"})
    size1 = os.path.getsize(f"user_states/{user_id}.bin")

    # Second request should reuse/update the same state
    client.post("/generate", json={"user_id": user_id, "prompt": "Again"})
    size2 = os.path.getsize(f"user_states/{user_id}.bin")

    # State should still be valid and non-empty
    assert size1 > 0
    assert size2 > 0


def test_multiple_users_have_isolated_states(client):
    """ Verify that each user has an independent state file."""
    users = ["a", "b", "c"]

    # Generate state for multiple users
    for user_id in users:
        client.post("/generate", json={"user_id": user_id, "prompt": "hi"})

    files = os.listdir("user_states")

    # Check one file per user
    assert len(files) == len(users)

    for user_id in users:
        assert f"{user_id}.bin" in files


### TODO : memory test
'''

# In same context
curl -s http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" -H "X-User-Id: test" -d '{
  "messages": [
    {"role": "user", "content": "Je m appelle Fabien"},
    {"role": "user", "content": "C est quoi mon prenom ?"}
  ]
}'


# In 2 differents context
curl -s http://localhost:8000/v1/chat/completions \
-H "Content-Type: application/json" \
-H "X-User-Id: test" \
-d '{
  "messages": [
    {"role": "user", "content": "Je m appelle Fabien"}
  ]
}'

curl -s http://localhost:8000/v1/chat/completions \
-H "Content-Type: application/json" \
-H "X-User-Id: test" \
-d '{
  "messages": [
    {"role": "user", "content": "C est quoi mon prenom ?"}
  ]
}'


curl http://127.0.0.1:8001/slots
# verifier si n_prompt_tokens_processed == n_prompt_tokens ?
'''