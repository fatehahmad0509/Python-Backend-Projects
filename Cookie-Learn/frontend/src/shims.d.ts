declare module "@/components/ui/sheet" {
  export const Sheet: any;
  export const SheetTrigger: any;
  export const SheetClose: any;
  export const SheetContent: any;
  export const SheetHeader: any;
  export const SheetFooter: any;
  export const SheetTitle: any;
  export const SheetDescription: any;
}

declare module "@/components/ui/dialog" {
  export const Dialog: any;
  export const DialogTrigger: any;
  export const DialogContent: any;
  export const DialogHeader: any;
  export const DialogFooter: any;
  export const DialogTitle: any;
  export const DialogDescription: any;
}

declare module "@/components/ui/tabs" {
  export const Tabs: any;
  export const TabsList: any;
  export const TabsTrigger: any;
  export const TabsContent: any;
}

declare module "@/components/ui/progress" {
  export const Progress: any;
}

declare module "@/components/ui/sonner" {
  export const Toaster: any;
}

declare module "@/components/ui/*" {
  const anything: any;
  export default anything;
  export = anything;
}

declare module "*.css";
