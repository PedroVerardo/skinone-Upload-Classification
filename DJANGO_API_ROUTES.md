## Auth

- POST /auth/register/
  - Request: { name, email, password, coren, specialty, institution }
  - Response: 201 Created, { id, name, email }

- POST /auth/login/
  - Request: { email, password }
  - Response: 200 OK, { token, user: { id, name, email } }


## Images

- GET /images/
  - Auth required
  - Response: 200 OK, [ { id, url } ] 

- POST /images/upload/
  - Auth required
  - Multipart form
  - Field: images (repeatable) -> multiple files allowed
  - Response: 201 Created, { upload_batch_id, uploaded }

- POST /images/upload/single/
  - Auth required
  - Multipart form
  - Field: image
  - Response: 201 Created, { image: { id, url } }

- POST /images/upload/with-stage/?stage=<estagio>
  - Auth required
  - Multipart form
  - Field: images (repeatable)
  - Query param: stage: "stage1"|"stage2"|"stage3"|"stage4"|"not_classifiable"|"dtpi"
  - Efeito: cria imagens e já registra classificação para cada uma
  - Response: 201 Created, { upload_batch_id, uploaded, stage, classified }

## Classifications

- POST /classifications/
  - Auth required
  - Request: { image_id: string, stage: "estagio1"|"estagio2"|"estagio3"|"estagio4"|"nao_classificavel"|"dtpi", observations?: string }
  - Response: 201 Created, { id, image_id, stage, created_at }

- GET /classifications/?image_id=<id>
  - Auth required
  - Response: 200 OK, [ { id, image_id, stage, created_at } ]

## Admin

- GET /admin/metrics/
  - Auth required (admin only)
  - Query params (opcional): `from=YYYY-MM-DD&to=YYYY-MM-DD`
  - Response: 200 OK
    - {
      total_users: number,
      total_images: number,
      classified_images_count: number,
      unclassified_images_count: number,
      classifications_per_category: { [stage: string]: number },
      classifications_by_user: [ { id, name, email, classification_count, last_active? } ],
      daily_classifications?: [ { date: string, count: number } ]
    }

- GET /admin/users/
  - Auth required (admin only)
  - Query params (opcional): `q`, `limit`, `offset`
  - Response: 200 OK, [ { id, name, email, classification_count, last_active? } ]

## Errors

Return JSON errors with proper HTTP status and a message field:

```
{ "message": "Validation failed", "errors": { "field": ["error"] } }
```


## Auth Notes
- put the error in the right format
- need to add a way to send the information to the front-end renders the image, the process in not in the same local
- Prefer `django-rest-framework` + `djangorestframework-simplejwt` or equivalent.
- Login returns an access token; the frontend stores it only in `localStorage` right now.
- All protected endpoints should require `Authorization: Bearer <token>`.
