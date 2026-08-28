def create_organisation(client, name="Viva con Agua"):
    resp = client.post("/v1/organisations", json={"name": name, "email": "org@example.com"})
    assert resp.status_code == 201
    return resp.get_json()["payload"]


def create_crew(client, organisation_id, name="Hamburg"):
    resp = client.post(
        "/v1/crews",
        json={
            "name": name,
            "organisation_id": organisation_id,
            "cities": [{"city": "Hamburg", "country": "Germany", "country_code": "DE",
                        "position": {"lat": 53.55, "lng": 9.99}}],
        },
    )
    assert resp.status_code == 201
    return resp.get_json()["payload"]


def create_user(client, crew_id=None, organisation_id=None, email="jane@example.com"):
    resp = client.post(
        "/v1/users",
        json={
            "email": email,
            "first_name": "Jane",
            "last_name": "Doe",
            "crew_id": crew_id,
            "organisation_id": organisation_id,
        },
    )
    assert resp.status_code == 201
    return resp.get_json()["payload"]


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_organisation_crud(client):
    org = create_organisation(client)
    assert org["name"] == "Viva con Agua"

    resp = client.get(f"/v1/organisations/{org['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["payload"]["id"] == org["id"]

    resp = client.put(f"/v1/organisations/{org['id']}", json={"name": "VcA e.V."})
    assert resp.status_code == 200
    assert resp.get_json()["payload"]["name"] == "VcA e.V."

    resp = client.get("/v1/organisations", query_string={"name": "VcA"})
    assert resp.status_code == 200
    assert resp.get_json()["meta"]["total"] == 1

    resp = client.delete(f"/v1/organisations/{org['id']}")
    assert resp.status_code == 200
    assert client.get(f"/v1/organisations/{org['id']}").status_code == 404


def test_crew_with_cities_and_public_listing(client):
    org = create_organisation(client)
    crew = create_crew(client, org["id"])

    assert crew["organisation"]["id"] == org["id"]
    assert len(crew["cities"]) == 1
    assert crew["cities"][0]["position"] == {"lat": 53.55, "lng": 9.99}

    resp = client.get("/v1/crews/public")
    assert resp.status_code == 200
    payload = resp.get_json()["payload"]
    assert len(payload) == 1
    assert "email" not in payload[0]


def test_user_address_and_roles(client):
    org = create_organisation(client)
    crew = create_crew(client, org["id"])
    user = create_user(client, crew_id=crew["id"], organisation_id=org["id"])

    resp = client.post(
        "/v1/addresses",
        json={
            "user_id": user["id"],
            "street": "Reeperbahn",
            "number": "1",
            "zip": "20359",
            "city": "Hamburg",
            "country": "Germany",
            "country_code": "DE",
        },
    )
    assert resp.status_code == 201
    address = resp.get_json()["payload"]
    assert address["user_id"] == user["id"]

    # A second address for the same user must be rejected (one-to-one).
    resp = client.post(
        "/v1/addresses",
        json={
            "user_id": user["id"],
            "street": "Second St",
            "number": "2",
            "zip": "20359",
            "city": "Hamburg",
            "country": "Germany",
            "country_code": "DE",
        },
    )
    assert resp.status_code == 409

    resp = client.get(f"/v1/users/{user['id']}")
    assert resp.status_code == 200
    fetched = resp.get_json()["payload"]
    assert fetched["address"]["id"] == address["id"]
    assert fetched["full_name"] == "Jane Doe"

    resp = client.post("/v1/roles", json={"user_id": user["id"], "name": "asp", "crew_id": crew["id"]})
    assert resp.status_code == 201
    role = resp.get_json()["payload"]
    assert role["name"] == "asp"

    # Duplicate role assignment is rejected.
    resp = client.post("/v1/roles", json={"user_id": user["id"], "name": "asp"})
    assert resp.status_code == 409

    resp = client.get("/v1/roles", query_string={"user_id": user["id"]})
    assert resp.status_code == 200
    assert len(resp.get_json()["payload"]) == 1

    resp = client.delete(f"/v1/roles/{role['id']}")
    assert resp.status_code == 200
    assert client.get("/v1/roles", query_string={"user_id": user["id"]}).get_json()["payload"] == []


def test_role_bulk_assignment(client):
    org = create_organisation(client)
    crew = create_crew(client, org["id"])
    user_a = create_user(client, crew_id=crew["id"], organisation_id=org["id"], email="a@example.com")
    user_b = create_user(client, crew_id=crew["id"], organisation_id=org["id"], email="b@example.com")

    resp = client.post(
        "/v1/roles/bulk",
        json={"crew_id": crew["id"], "user_ids": [user_a["id"], user_b["id"]], "name": "finance"},
    )
    assert resp.status_code == 201
    payload = resp.get_json()["payload"]
    assert len(payload["created"]) == 2
    assert payload["skipped"] == []

    # Re-running the bulk assignment should skip both now-existing roles.
    resp = client.post(
        "/v1/roles/bulk",
        json={"crew_id": crew["id"], "user_ids": [user_a["id"], user_b["id"]], "name": "finance"},
    )
    payload = resp.get_json()["payload"]
    assert payload["created"] == []
    assert len(payload["skipped"]) == 2


def test_validation_error_returns_400(client):
    resp = client.post("/v1/organisations", json={"email": "not-a-real-org"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_not_found_returns_404(client):
    resp = client.get("/v1/users/does-not-exist")
    assert resp.status_code == 404
