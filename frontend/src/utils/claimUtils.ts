// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function createClaimsTable(idTokenClaims: any): Record<string, [string, string, string]> {
  const claims: Record<string, [string, string, string]> = {};

  if (!idTokenClaims) {
    return claims;
  }

  const claimDescriptions: Record<string, string> = {
    aud: "Audience - The intended recipient of the token",
    exp: "Expiration time - When the token expires (Unix timestamp)",
    iat: "Issued at - When the token was issued (Unix timestamp)",
    iss: "Issuer - The entity that issued the token",
    nbf: "Not before - Token is not valid before this time (Unix timestamp)",
    sub: "Subject - The principal that the token is about",
    ver: "Version - The version of the token",
    name: "Name - The user's full name",
    preferred_username: "Preferred username - The user's preferred username",
    email: "Email - The user's email address",
    oid: "Object ID - The unique identifier for the user",
    tid: "Tenant ID - The unique identifier for the Azure AD tenant",
    upn: "User Principal Name - The user's UPN",
    roles: "Roles - The roles assigned to the user",
    groups: "Groups - The groups the user belongs to",
    acr: "Authentication context class reference",
    aio: "Azure AD internal claim",
    amr: "Authentication methods reference",
    appid: "Application ID - The unique identifier for the application",
    appidacr: "Application ID authentication context class reference",
    family_name: "Family name - The user's last name",
    given_name: "Given name - The user's first name",
    ipaddr: "IP address - The IP address of the client",
    onprem_sid: "On-premises security identifier",
    puid: "Platform user identifier",
    scp: "Scopes - The scopes granted to the token",
    unique_name: "Unique name - The unique name of the user",
    uti: "Unique token identifier",
    xms_st: "XMS security token",
    xms_tcdt: "XMS token creation date time",
  };

  for (const [key, value] of Object.entries(idTokenClaims)) {
    let displayValue = String(value);

    // Format dates if they're Unix timestamps
    if (key === "exp" || key === "iat" || key === "nbf" || key === "xms_tcdt") {
      const timestamp = Number(value);
      if (!isNaN(timestamp)) {
        displayValue = new Date(timestamp * 1000).toLocaleString();
      }
    }

    // Format arrays
    if (Array.isArray(value)) {
      displayValue = value.join(", ");
    }

    // Format objects
    if (typeof value === "object" && value !== null && !Array.isArray(value)) {
      displayValue = JSON.stringify(value, null, 2);
    }

    claims[key] = [
      key,
      displayValue,
      claimDescriptions[key] || "No description available",
    ];
  }

  return claims;
}
