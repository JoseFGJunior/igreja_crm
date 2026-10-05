# Elo Perfeito Mobile — PIB Cruz

Aplicativo React Native/Expo público da Primeira Igreja Batista em Cruz de Rebouças.

## Rodar

```bash
npm install
npx expo start
```

Defina `EXPO_PUBLIC_API_BASE_URL` apontando para o backend Django. O app usa o tenant fixo `pibcruz` e consome `GET /api/mobile/v1/home/`.

A tela usa fallback visual enquanto a API está indisponível, mas não solicita login nem seleção de igreja.