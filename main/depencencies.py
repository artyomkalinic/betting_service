from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from token_settings import verify_token

# URL для получения токена (например, "/token")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)  # Ваша функция проверки токена
        return payload  # Возвращаем полезную нагрузку токена
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось проверить учетные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )
