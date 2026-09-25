import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useRef,
} from "react";
import { AssignmentsAPI, CoursesAPI, ProgressAPI, TenantsAPI, UsersAPI } from "./api.js";

// Central data store: owns all server state, keyed + cached.
// Every mutation invalidates/re-fetches affected slices so the UI
// updates immediately — never requires a manual refresh.
// (No React Query/SWR in package.json, so this minimal store covers it.)

const StoreCtx = createContext(null);

const initialState = {
  cache: {}, // key -> { data, updatedAt }
  loading: {}, // key -> bool
  errors: {}, // key -> Error|null
  versions: {}, // key -> number (bump to refetch)
};

function reducer(state, action) {
  switch (action.type) {
    case "FETCH_START":
      return { ...state, loading: { ...state.loading, [action.key]: true }, errors: { ...state.errors, [action.key]: null } };
    case "FETCH_OK":
      return {
        ...state,
        loading: { ...state.loading, [action.key]: false },
        cache: { ...state.cache, [action.key]: { data: action.data, updatedAt: Date.now() } },
      };
    case "FETCH_ERR":
      return {
        ...state,
        loading: { ...state.loading, [action.key]: false },
        errors: { ...state.errors, [action.key]: action.error },
      };
    case "INVALIDATE": {
      const versions = { ...state.versions };
      for (const k of action.keys) versions[k] = (versions[k] || 0) + 1;
      return { ...state, versions };
    }
    case "OPTIMISTIC":
      return {
        ...state,
        cache: { ...state.cache, [action.key]: { data: action.data, updatedAt: Date.now() } },
      };
    default:
      return state;
  }
}

const FETCHERS = {
  users: () => UsersAPI.list(),
  tenants: () => TenantsAPI.list(),
  courses: () => CoursesAPI.list(),
  assignments: () => AssignmentsAPI.list(),
  progress: () => ProgressAPI.list(),
};

function courseKey(id) {
  return `course:${id}`;
}

export function StoreProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const inFlight = useRef({});

  const fetchKey = useCallback(
    async (key, force = false) => {
      const fetcher =
        FETCHERS[key] ||
        (key.startsWith("course:")
          ? () => CoursesAPI.get(key.slice("course:".length))
          : null);
      if (!fetcher) return null;
      if (!force && state.cache[key] && !state.versions[key]) {
        // cached; versions bump forces refetch even when cached
      }
      if (inFlight.current[key]) return inFlight.current[key];
      dispatch({ type: "FETCH_START", key });
      const p = (async () => {
        try {
          const data = await fetcher();
          dispatch({ type: "FETCH_OK", key, data });
          return data;
        } catch (e) {
          dispatch({ type: "FETCH_ERR", key, error: e });
          throw e;
        } finally {
          delete inFlight.current[key];
        }
      })();
      inFlight.current[key] = p;
      return p;
    },
    [state.cache, state.versions]
  );

  const invalidate = useCallback((keys) => {
    dispatch({ type: "INVALIDATE", keys });
  }, []);

  // Refetch a key whenever its version bumps.
  const versionsJson = JSON.stringify(state.versions);
  useEffect(() => {
    const versions = JSON.parse(versionsJson);
    for (const key of Object.keys(versions)) {
      fetchKey(key, true).catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [versionsJson]);

  // ---- Mutations: persist via API, then invalidate affected slices ----

  const createCourse = useCallback(
    async (payload) => {
      const created = await CoursesAPI.create(payload);
      invalidate(["courses"]);
      return created;
    },
    [invalidate]
  );
  const updateCourse = useCallback(
    async (id, payload) => {
      const updated = await CoursesAPI.update(id, payload);
      invalidate(["courses", courseKey(id)]);
      return updated;
    },
    [invalidate]
  );
  const deleteCourse = useCallback(
    async (id) => {
      await CoursesAPI.remove(id);
      invalidate(["courses", "assignments", "progress"]);
    },
    [invalidate]
  );

  const createUser = useCallback(
    async (payload) => {
      const created = await UsersAPI.create(payload);
      invalidate(["users"]);
      return created;
    },
    [invalidate]
  );
  const updateUser = useCallback(
    async (id, payload) => {
      const updated = await UsersAPI.update(id, payload);
      invalidate(["users"]);
      return updated;
    },
    [invalidate]
  );
  const deleteUser = useCallback(
    async (id) => {
      await UsersAPI.remove(id);
      invalidate(["users", "assignments", "progress"]);
    },
    [invalidate]
  );

  const createAssignment = useCallback(
    async (payload) => {
      const created = await AssignmentsAPI.create(payload);
      invalidate(["assignments", "progress", "courses"]);
      return created;
    },
    [invalidate]
  );
  const deleteAssignment = useCallback(
    async (id) => {
      await AssignmentsAPI.remove(id);
      invalidate(["assignments", "progress", "courses"]);
    },
    [invalidate]
  );

  const updateProgress = useCallback(
    async (id, pct, opts = {}) => {
      const key = "progress";
      const prev = state.cache[key]?.data;
      // Optimistic update so the progress bar moves immediately.
      if (Array.isArray(prev)) {
        const next = prev.map((p) => (p.id === id ? { ...p, progress_percentage: pct } : p));
        dispatch({ type: "OPTIMISTIC", key, data: next });
      }
      try {
        const updated = await ProgressAPI.update(id, pct);
        invalidate(["progress", "assignments"]);
        if (opts.courseId) invalidate([courseKey(opts.courseId)]);
        return updated;
      } catch (e) {
        // Reconcile with server on failure.
        invalidate(["progress"]);
        throw e;
      }
    },
    [invalidate, state.cache]
  );

  const createTenant = useCallback(
    async (payload) => {
      const created = await TenantsAPI.create(payload);
      invalidate(["tenants"]);
      return created;
    },
    [invalidate]
  );

  const value = useMemo(
    () => ({
      cache: state.cache,
      loading: state.loading,
      errors: state.errors,
      fetchKey,
      invalidate,
      createCourse,
      updateCourse,
      deleteCourse,
      createUser,
      updateUser,
      deleteUser,
      createAssignment,
      deleteAssignment,
      updateProgress,
      createTenant,
    }),
    [
      state.cache,
      state.loading,
      state.errors,
      fetchKey,
      invalidate,
      createCourse,
      updateCourse,
      deleteCourse,
      createUser,
      updateUser,
      deleteUser,
      createAssignment,
      deleteAssignment,
      updateProgress,
      createTenant,
    ]
  );

  return <StoreCtx.Provider value={value}>{children}</StoreCtx.Provider>;
}

export function useStore() {
  const ctx = useContext(StoreCtx);
  if (!ctx) throw new Error("useStore must be used inside StoreProvider");
  return ctx;
}

// Hook: subscribe to a cached query; fetches on mount.
export function useQuery(key) {
  const { cache, loading, errors, fetchKey } = useStore();
  useEffect(() => {
    fetchKey(key).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return {
    data: cache[key]?.data ?? null,
    loading: !!loading[key] && !cache[key],
    error: errors[key] || null,
    refreshing: !!loading[key],
  };
}
