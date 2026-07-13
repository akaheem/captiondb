import { Mail, Shield, BadgeCheck, CircleAlert } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import type { UserDTO } from "@/types/api";

const PROVIDER_LABELS: Record<string, string> = {
  email: "Email & password",
  oauth: "OAuth",
  google: "Google",
  github: "GitHub",
  apple: "Apple",
  microsoft: "Microsoft",
  twitter: "Twitter",
};

function providerLabel(provider: string, oauthProvider: string | null): string {
  if (oauthProvider) return PROVIDER_LABELS[oauthProvider] ?? oauthProvider;
  return PROVIDER_LABELS[provider] ?? provider;
}

/** Read-only profile summary for the current user. */
export function ProfileCard({ user }: { user: UserDTO }) {
  const initials =
    user.username?.substring(0, 2).toUpperCase() ||
    user.email?.substring(0, 2).toUpperCase() ||
    "US";

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profile</CardTitle>
        <CardDescription>Your account details.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center gap-4">
          <Avatar className="h-16 w-16">
            <AvatarImage src={user.avatar_url ?? ""} alt={user.username} />
            <AvatarFallback className="text-lg">{initials}</AvatarFallback>
          </Avatar>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-lg font-semibold">
                {user.display_name || user.username}
              </span>
              {user.verified ? (
                <Badge variant="success">
                  <BadgeCheck className="h-3 w-3" />
                  Verified
                </Badge>
              ) : (
                <Badge variant="warning">
                  <CircleAlert className="h-3 w-3" />
                  Unverified
                </Badge>
              )}
            </div>
            <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <Mail className="h-3.5 w-3.5" />
              {user.email}
            </p>
          </div>
        </div>

        <Separator />

        <dl className="grid grid-cols-2 gap-x-4 gap-y-4 text-sm">
          <div>
            <dt className="font-medium text-muted-foreground">Username</dt>
            <dd>{user.username}</dd>
          </div>
          <div>
            <dt className="font-medium text-muted-foreground">Role</dt>
            <dd className="flex items-center gap-1.5">
              <Shield className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="capitalize">{user.role}</span>
            </dd>
          </div>
          <div>
            <dt className="font-medium text-muted-foreground">
              Account status
            </dt>
            <dd className="capitalize">{user.status.replace(/_/g, " ")}</dd>
          </div>
          <div>
            <dt className="font-medium text-muted-foreground">Display name</dt>
            <dd>{user.display_name || "—"}</dd>
          </div>
        </dl>

        <Separator />

        <div className="space-y-2">
          <p className="text-sm font-medium">Linked sign-in methods</p>
          {user.identities.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No sign-in methods linked.
            </p>
          ) : (
            <ul className="flex flex-wrap gap-2">
              {user.identities.map((identity) => (
                <li key={`${identity.provider}-${identity.provider_id}`}>
                  <Badge variant="outline">
                    {providerLabel(identity.provider, identity.oauth_provider)}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
