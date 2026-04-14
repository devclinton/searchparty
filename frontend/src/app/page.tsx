import { useTranslations } from "next-intl";

export default function Home() {
  const t = useTranslations();

  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-center gap-8 py-32 px-16 bg-white dark:bg-black">
        <div className="flex flex-col items-center gap-4 text-center">
          <h1 className="text-4xl font-bold tracking-tight text-black dark:text-zinc-50">
            {t("home.title")}
          </h1>
          <p className="text-xl text-zinc-600 dark:text-zinc-400">
            {t("home.subtitle")}
          </p>
          <p className="max-w-md text-base text-zinc-500 dark:text-zinc-500">
            {t("home.description")}
          </p>
        </div>
        <p className="max-w-lg text-center text-xs text-zinc-400 dark:text-zinc-600">
          {t("disclaimer.text")}
        </p>
      </main>
    </div>
  );
}
