export const fileValidators = {
  validatePDF: (file: File): string | null => {
    const maxBytes = 50 * 1024 * 1024;
    if (file.size > maxBytes) {
      return "PDF file size exceeds 50MB limit";
    }

    if (file.type !== "application/pdf") {
      return "File must be a PDF";
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      return "File must be a PDF (*.pdf)";
    }

    return null;
  },

  validateSealImage: (file: File): string | null => {
    const maxBytes = 5 * 1024 * 1024;
    if (file.size > maxBytes) {
      return "Seal image size exceeds 5MB limit";
    }

    const allowedTypes = ["image/png", "image/svg+xml"];
    if (!allowedTypes.includes(file.type)) {
      return "Seal image must be PNG or SVG";
    }

    const extension = file.name.toLowerCase().split(".").pop();
    if (!extension || !["png", "svg"].includes(extension)) {
      return "Seal image must be PNG or SVG (*.png, *.svg)";
    }

    return null;
  },

  validateCertificate: (file: File): string | null => {
    const maxBytes = 10 * 1024 * 1024;
    if (file.size > maxBytes) {
      return "Certificate file size exceeds 10MB limit";
    }

    const extension = file.name.toLowerCase().split(".").pop();
    if (!extension || !["p12", "pfx"].includes(extension)) {
      return "Certificate must be P12 or PFX (*.p12, *.pfx)";
    }

    return null;
  },
};
