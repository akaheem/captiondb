import { describe, expect, it } from "vitest";
import { loginSchema, registerSchema } from "@/lib/validations/auth";

describe("loginSchema", () => {
  it("accepts a valid email and password", () => {
    const r = loginSchema.safeParse({
      email: "user@example.com",
      password: "hunter2!",
    });
    expect(r.success).toBe(true);
  });

  it("rejects a malformed email", () => {
    const r = loginSchema.safeParse({ email: "nope", password: "hunter2!" });
    expect(r.success).toBe(false);
  });

  it("rejects passwords shorter than 8 characters", () => {
    const r = loginSchema.safeParse({
      email: "user@example.com",
      password: "short",
    });
    expect(r.success).toBe(false);
  });
});

describe("registerSchema", () => {
  const valid = {
    email: "user@example.com",
    username: "cool_user-1",
    password: "Password1",
    confirmPassword: "Password1",
  };

  it("accepts a fully valid registration", () => {
    expect(registerSchema.safeParse(valid).success).toBe(true);
  });

  it("requires an uppercase letter and a digit in the password", () => {
    expect(
      registerSchema.safeParse({
        ...valid,
        password: "password",
        confirmPassword: "password",
      }).success
    ).toBe(false);
    expect(
      registerSchema.safeParse({
        ...valid,
        password: "PASSWORD",
        confirmPassword: "PASSWORD",
      }).success
    ).toBe(false);
  });

  it("rejects usernames with illegal characters", () => {
    expect(
      registerSchema.safeParse({ ...valid, username: "bad name!" }).success
    ).toBe(false);
  });

  it("flags mismatched confirmation on the confirmPassword path", () => {
    const r = registerSchema.safeParse({
      ...valid,
      confirmPassword: "Different1",
    });
    expect(r.success).toBe(false);
    if (!r.success) {
      expect(r.error.issues.some((i) => i.path.includes("confirmPassword"))).toBe(
        true
      );
    }
  });
});
