FROM microsoft/dotnet:2.0-sdk-stretch AS builder

WORKDIR /app
COPY *.csproj ./
RUN dotnet restore
COPY *.cs ./
RUN dotnet publish -c Release -o out

FROM microsoft/dotnet:2.0-runtime-stretch

WORKDIR /app
COPY --from=builder /app/out ./

ENTRYPOINT ["dotnet", "FaceApi.dll"]
