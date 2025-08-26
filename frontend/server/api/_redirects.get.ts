import { readFileSync } from "fs";
import { join } from "path";

/**
 * API endpoint to serve redirect configuration
 * GET /api/_redirects
 */
export default defineEventHandler(async (event) => {
    try {
        const configPath = join(process.cwd(), "config", "redirects.json");
        const configContent = readFileSync(configPath, "utf-8");
        const config = JSON.parse(configContent);

        return config;
    } catch (error) {
        console.error("Failed to load redirect configuration:", error);

        // Return empty configuration on error
        return {
            redirects: {},
        };
    }
});
