import { Router, type IRouter } from "express";
import healthRouter from "./health";
import authRouter from "./auth";
import apiManagerRouter from "./apiManager";
import userManagerRouter from "./userManager";
import dynamicApiRouter from "./dynamicApi";
import bloxfruitRouter from "./bloxfruit";

const router: IRouter = Router();

router.use(healthRouter);
router.use("/auth", authRouter);
router.use("/manage", apiManagerRouter);
router.use("/manage", userManagerRouter);
router.use(dynamicApiRouter);
router.use(bloxfruitRouter);

export default router;
