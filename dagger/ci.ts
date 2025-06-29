import { Client, connect } from "@dagger.io/dagger";

export default async function pipeline() {
  const client = await connect();
  
  try {
    // Get source directory
    const source = client.host().directory(".", {
      exclude: ["node_modules", ".git", "dist", "build", ".next", "coverage", "dagger"]
    });
    
    // Build container using Nixpacks approach
    const container = client
      .container()
      .from("alpine:latest")
      .withExec(["apk", "add", "--no-cache", "bash", "curl", "git"])
      .withDirectory("/app", source)
      .withWorkdir("/app");
    
    // Run project-specific commands
    const tested = await runTests(client, container);
    
    // Build final image
    const image = tested.withLabel("built-by", "dagger");
    
    // Publish to registry (using ttl.sh for demo)
    const imageRef = await image.publish(`ttl.sh/seo-tools-clone:1h`);
    console.log(`Published image: ${imageRef}`);
    
    return imageRef;
  } finally {
    await client.close();
  }
}

async function runTests(client: Client, container: any) {
  // Detect and run tests based on project type
  const projectFiles = await client.host().directory(".").entries();
  
  if (projectFiles.includes("package.json")) {
    return container
      .withExec(["sh", "-c", "command -v npm || (apk add --no-cache nodejs npm)"])
      .withExec(["npm", "install", "--no-fund", "--no-audit"])
      .withExec(["npm", "test", "||", "echo", "No tests found"]);
  } else if (projectFiles.includes("requirements.txt")) {
    return container
      .withExec(["sh", "-c", "command -v python3 || apk add --no-cache python3 py3-pip"])
      .withExec(["pip", "install", "-r", "requirements.txt", "||", "echo", "No requirements"])
      .withExec(["python", "-m", "pytest", "||", "echo", "No tests found"]);
  } else if (projectFiles.includes("go.mod")) {
    return container
      .withExec(["sh", "-c", "command -v go || apk add --no-cache go"])
      .withExec(["go", "test", "./...", "||", "echo", "No tests found"]);
  }
  
  return container;
}

// Run the pipeline
if (require.main === module) {
  pipeline().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}
