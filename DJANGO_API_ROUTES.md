# Django API Routes for Skin One Frontend

Base URL: `${VITE_API_BASE_URL}`

All JSON responses should use `application/json`. Use JWT or token-based auth; the frontend sends `Authorization: Bearer <token>` when logged in.

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
  - Response: 200 OK, [ { id, url, patient? } ] //Aqui no caso seria path ao invez de url, ou eu deveria enviar todas as imagens?

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
  - Query param: stage: "estagio1"|"estagio2"|"estagio3"|"estagio4"|"nao_classificavel"|"dtpi"
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

esta feito como sucsses and error
```
{
            'success': False,
            'error': 'Internal server error'
        }
```
