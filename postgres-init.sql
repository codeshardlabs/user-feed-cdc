CREATE TYPE "public"."mode" AS ENUM('normal', 'collaboration'); 
CREATE TYPE "public"."template_type" AS ENUM('static', 'angular', 'react', 'react-ts', 'solid', 'svelte', 'test-ts', 'vanilla-ts', 'vanilla', 'vue', 'vue-ts', 'node', 'nextjs', 'astro', 'vite', 'vite-react', 'vite-react-ts'); 
CREATE TYPE "public"."type" AS ENUM('public', 'private', 'forked'); 
CREATE TABLE "comments" (
	"id" serial PRIMARY KEY NOT NULL,
	"message" text NOT NULL,
	"user_id" text NOT NULL,
	"shard_id" serial NOT NULL,
	"updated_at" timestamp,
	"created_at" timestamp DEFAULT now() NOT NULL
);

CREATE TABLE "replies" (
	"id" serial PRIMARY KEY NOT NULL,
	"comment_id" serial NOT NULL,
	"parent_id" serial NOT NULL
);
 
CREATE TABLE "dependencies" (
	"id" serial PRIMARY KEY NOT NULL,
	"name" text,
	"version" text,
	"is_dev_dependency" boolean,
	"shard_id" serial NOT NULL,
	"updated_at" timestamp,
	"created_at" timestamp DEFAULT now() NOT NULL
);
 
CREATE TABLE "files" (
	"id" serial PRIMARY KEY NOT NULL,
	"name" text,
	"code" text,
	"hash" integer DEFAULT 0,
	"read_only" boolean DEFAULT false,
	"hidden" boolean DEFAULT false,
	"shard_id" serial NOT NULL,
	"updated_at" timestamp,
	"created_at" timestamp DEFAULT now() NOT NULL
);
 
CREATE TABLE "likes" (
	"id" serial PRIMARY KEY NOT NULL,
	"shard_id" serial NOT NULL,
	"liked_by" text NOT NULL,
	"updated_at" timestamp,
	"created_at" timestamp DEFAULT now() NOT NULL
);
 
CREATE TABLE "shards" (
	"id" serial PRIMARY KEY NOT NULL,
	"title" text DEFAULT 'Untitled',
	"user_id" text NOT NULL,
	"templateType" "template_type" DEFAULT 'react',
	"mode" "mode" DEFAULT 'normal',
	"type" "type" DEFAULT 'public',
	"last_sync_timestamp" timestamp DEFAULT now(),
	"updated_at" timestamp,
	"created_at" timestamp DEFAULT now() NOT NULL
);
 
CREATE TABLE "followers" (
	"id" serial PRIMARY KEY NOT NULL,
	"follower_id" text NOT NULL,
	"following_id" text NOT NULL,
	"updated_at" timestamp,
	"created_at" timestamp DEFAULT now() NOT NULL
);
 
CREATE TABLE "users" (
	"id" text PRIMARY KEY NOT NULL,
	"updated_at" timestamp,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoinr
ALTER TABLE "comments" ADD CONSTRAINT "comments_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action; 
ALTER TABLE "comments" ADD CONSTRAINT "comments_shard_id_shards_id_fk" FOREIGN KEY ("shard_id") REFERENCES "public"."shards"("id") ON DELETE cascade ON UPDATE no action; 
ALTER TABLE "replies" ADD CONSTRAINT "replies_comment_id_comments_id_fk" FOREIGN KEY ("comment_id") REFERENCES "public"."comments"("id") ON DELETE cascade ON UPDATE no action; 
ALTER TABLE "replies" ADD CONSTRAINT "replies_parent_id_comments_id_fk" FOREIGN KEY ("parent_id") REFERENCES "public"."comments"("id") ON DELETE cascade ON UPDATE no action; 
ALTER TABLE "dependencies" ADD CONSTRAINT "dependencies_shard_id_shards_id_fk" FOREIGN KEY ("shard_id") REFERENCES "public"."shards"("id") ON DELETE cascade ON UPDATE no action; 
ALTER TABLE "files" ADD CONSTRAINT "files_shard_id_shards_id_fk" FOREIGN KEY ("shard_id") REFERENCES "public"."shards"("id") ON DELETE cascade ON UPDATE no action; 
ALTER TABLE "likes" ADD CONSTRAINT "likes_shard_id_shards_id_fk" FOREIGN KEY ("shard_id") REFERENCES "public"."shards"("id") ON DELETE cascade ON UPDATE no action; 
ALTER TABLE "likes" ADD CONSTRAINT "likes_liked_by_users_id_fk" FOREIGN KEY ("liked_by") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action; 
ALTER TABLE "shards" ADD CONSTRAINT "shards_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action; 
ALTER TABLE "followers" ADD CONSTRAINT "followers_follower_id_users_id_fk" FOREIGN KEY ("follower_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action; 
ALTER TABLE "followers" ADD CONSTRAINT "followers_following_id_users_id_fk" FOREIGN KEY ("following_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action; 
CREATE INDEX "comm_shard_id_index" ON "comments" USING btree ("shard_id"); 
CREATE INDEX "dep_shard_id_index" ON "dependencies" USING btree ("shard_id"); 
CREATE INDEX "file_shard_id_index" ON "files" USING btree ("shard_id"); 
CREATE INDEX "like_shard_id_index" ON "likes" USING btree ("shard_id");


-- create users 
INSERT INTO "users" ("id") VALUES ('1'), ('2'), ('3'), ('4'), ('5');

-- create shards
INSERT INTO "shards" ("id", "user_id", "title", "mode", "type") VALUES 
(1, '1', 'My First Shard', 'normal', 'public'),
(2, '2', 'My Second Shard', 'collaboration', 'public'),
(3, '3', 'My Third Shard', 'normal', 'public'),
(4, '4', 'My Fourth Shard', 'collaboration', 'public'),
(5, '5', 'My Fifth Shard', 'normal', 'public');

-- follow users
INSERT INTO "followers" ("follower_id", "following_id") VALUES 
('1', '2');

-- required for debezium
CREATE PUBLICATION "codeshard_publication" FOR TABLE "likes", "shards", "followers", "comments";